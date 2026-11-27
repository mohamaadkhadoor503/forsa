"""Freelance project workflow: submit, accept/reject, complete."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext as _

from apps.core.services.stats import invalidate_stats
from apps.notifications.models import Notification
from apps.notifications.services.notifier import NotificationService
from apps.projects.models import Project, Proposal


class ProposalService:
    def __init__(self, notifier: NotificationService | None = None):
        self.notifier = notifier or NotificationService()

    @transaction.atomic
    def submit(self, *, project, freelancer, cover_letter, bid_amount, delivery_days):
        if not freelancer.is_seeker:
            raise PermissionDenied
        if project.status != Project.Status.OPEN:
            raise ValidationError(_("المشروع لا يستقبل عروضاً حالياً."))
        if Proposal.objects.filter(project=project, freelancer=freelancer).exists():
            raise ValidationError(_("لقد قدمت عرضاً على هذا المشروع مسبقاً."))
        proposal = Proposal.objects.create(project=project, freelancer=freelancer, cover_letter=cover_letter,
                                           bid_amount=bid_amount, delivery_days=delivery_days)
        self.notifier.notify(
            project.owner, _("عرض جديد على مشروع %(p)s") % {"p": project.title},
            _("%(name)s قدم عرضاً بقيمة $%(amount)s") % {"name": freelancer.display_name, "amount": bid_amount},
            reverse("dashboard:employer_project_proposals", args=[project.pk]), Notification.Kind.PROPOSAL,
        )
        return proposal

    def _ensure_owner(self, proposal, actor):
        if proposal.project.owner_id != actor.id:
            raise PermissionDenied

    @transaction.atomic
    def accept(self, proposal, actor):
        self._ensure_owner(proposal, actor)
        project = proposal.project
        if project.status != Project.Status.OPEN:
            raise ValidationError(_("تم إسناد هذا المشروع مسبقاً."))
        proposal.status = Proposal.Status.ACCEPTED
        proposal.save(update_fields=["status", "updated_at"])
        project.proposals.exclude(pk=proposal.pk).filter(
            status__in=[Proposal.Status.PENDING, Proposal.Status.SHORTLISTED]
        ).update(status=Proposal.Status.REJECTED)
        project.status = Project.Status.IN_PROGRESS
        project.freelancer = proposal.freelancer
        project.save(update_fields=["status", "freelancer", "updated_at"])
        self.notifier.notify(
            proposal.freelancer, _("🎉 تم قبول عرضك!"),
            _("تم إسنادك لمشروع %(p)s") % {"p": project.title},
            reverse("dashboard:seeker_proposals"), Notification.Kind.SUCCESS,
        )
        invalidate_stats()
        return proposal

    @transaction.atomic
    def set_status(self, proposal, status, actor):
        self._ensure_owner(proposal, actor)
        if status not in (Proposal.Status.SHORTLISTED, Proposal.Status.REJECTED):
            raise ValidationError(_("حالة غير صالحة."))
        if proposal.status not in (Proposal.Status.PENDING, Proposal.Status.SHORTLISTED):
            raise ValidationError(_("لا يمكن تعديل هذا العرض."))
        proposal.status = status
        proposal.save(update_fields=["status", "updated_at"])
        self.notifier.notify(
            proposal.freelancer, _("تحديث على عرضك"),
            _("عرضك على %(p)s: %(s)s") % {"p": proposal.project.title, "s": proposal.get_status_display()},
            reverse("dashboard:seeker_proposals"), Notification.Kind.PROPOSAL,
        )
        return proposal

    @transaction.atomic
    def withdraw(self, proposal, actor):
        if proposal.freelancer_id != actor.id:
            raise PermissionDenied
        if proposal.status not in (Proposal.Status.PENDING, Proposal.Status.SHORTLISTED):
            raise ValidationError(_("لا يمكن سحب هذا العرض."))
        proposal.status = Proposal.Status.WITHDRAWN
        proposal.save(update_fields=["status", "updated_at"])
        return proposal


class ProjectService:
    @staticmethod
    @transaction.atomic
    def complete(project, actor):
        if project.owner_id != actor.id:
            raise PermissionDenied
        if project.status != Project.Status.IN_PROGRESS:
            raise ValidationError(_("يمكن إنهاء المشاريع قيد التنفيذ فقط."))
        project.status = Project.Status.COMPLETED
        project.save(update_fields=["status", "updated_at"])
        invalidate_stats()
        return project

    @staticmethod
    def cancel(project, actor):
        if project.owner_id != actor.id:
            raise PermissionDenied
        if project.status == Project.Status.COMPLETED:
            raise ValidationError(_("لا يمكن إلغاء مشروع مكتمل."))
        project.status = Project.Status.CANCELLED
        project.save(update_fields=["status", "updated_at"])
        return project
