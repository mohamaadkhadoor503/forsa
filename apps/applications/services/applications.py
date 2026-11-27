"""Job application use-cases: apply, change status, withdraw."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext as _

from apps.applications.models import Application, ApplicationEvent
from apps.core.services.stats import invalidate_stats
from apps.notifications.models import Notification
from apps.notifications.services.notifier import NotificationService

# Allowed transitions keep the workflow consistent.
TRANSITIONS = {
    Application.Status.SUBMITTED: {"reviewing", "shortlisted", "interview", "rejected"},
    Application.Status.REVIEWING: {"shortlisted", "interview", "rejected"},
    Application.Status.SHORTLISTED: {"interview", "offered", "rejected"},
    Application.Status.INTERVIEW: {"offered", "rejected", "shortlisted"},
    Application.Status.OFFERED: {"hired", "rejected"},
}


class ApplicationService:
    def __init__(self, notifier: NotificationService | None = None):
        self.notifier = notifier or NotificationService()

    @transaction.atomic
    def apply(self, *, job, applicant, cover_letter, cv=None, expected_salary=None) -> Application:
        if not applicant.is_seeker:
            raise PermissionDenied
        if not job.is_open:
            raise ValidationError(_("هذه الوظيفة لم تعد تستقبل طلبات."))
        if Application.objects.filter(job=job, applicant=applicant).exists():
            raise ValidationError(_("لقد تقدمت لهذه الوظيفة مسبقاً."))
        app = Application.objects.create(
            job=job, applicant=applicant, cover_letter=cover_letter,
            cv=cv or "", expected_salary=expected_salary,
        )
        ApplicationEvent.objects.create(application=app, status=app.status, created_by=applicant)
        self.notifier.notify(
            job.company.owner,
            _("طلب جديد على وظيفة %(job)s") % {"job": job.title},
            _("%(name)s تقدّم للوظيفة.") % {"name": applicant.display_name},
            reverse("dashboard:employer_job_applications", args=[job.pk]),
            Notification.Kind.APPLICATION,
        )
        return app

    @transaction.atomic
    def change_status(self, application, new_status, actor, note=""):
        if application.job.company.owner_id != actor.id and not actor.is_staff:
            raise PermissionDenied
        allowed = TRANSITIONS.get(application.status, set())
        if new_status not in allowed:
            raise ValidationError(_("لا يمكن نقل الطلب إلى هذه الحالة."))
        application.status = new_status
        application.save(update_fields=["status", "updated_at"])
        ApplicationEvent.objects.create(application=application, status=new_status, note=note, created_by=actor)
        label = Application.Status(new_status).label
        kind = Notification.Kind.SUCCESS if new_status in ("offered", "hired", "interview") else Notification.Kind.APPLICATION
        self.notifier.notify(
            application.applicant,
            _("تحديث على طلبك: %(job)s") % {"job": application.job.title},
            _("حالة الطلب الآن: %(status)s") % {"status": label},
            reverse("dashboard:seeker_applications"),
            kind,
        )
        if new_status == Application.Status.HIRED:
            invalidate_stats()
        return application

    @transaction.atomic
    def withdraw(self, application, actor):
        if application.applicant_id != actor.id:
            raise PermissionDenied
        if application.is_final:
            raise ValidationError(_("لا يمكن سحب هذا الطلب."))
        application.status = Application.Status.WITHDRAWN
        application.save(update_fields=["status", "updated_at"])
        ApplicationEvent.objects.create(application=application, status=application.status, created_by=actor)
        return application

    @staticmethod
    def allowed_transitions(application):
        return [(s, Application.Status(s).label) for s in TRANSITIONS.get(application.status, set())
                if s in Application.Status.values]
