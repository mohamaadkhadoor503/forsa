"""Resolve a reportable target from (type, id). Registry keeps it extensible."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext as _

from .models import Report, Review


def _job(pk):
    from apps.jobs.models import Job
    return Job.objects.filter(pk=pk).first()


def _project(pk):
    from apps.projects.models import Project
    return Project.objects.filter(pk=pk).first()


def _company(pk):
    from apps.companies.models import Company
    return Company.objects.filter(pk=pk).first()


def _profile(pk):
    from apps.talents.models import SeekerProfile
    return SeekerProfile.objects.filter(pk=pk).first()


TARGET_RESOLVERS = {
    Report.Target.JOB: _job,
    Report.Target.PROJECT: _project,
    Report.Target.COMPANY: _company,
    Report.Target.PROFILE: _profile,
}


class ReportService:
    @staticmethod
    def create(*, reporter, target_type, target_id, reason, details=""):
        resolver = TARGET_RESOLVERS.get(target_type)
        obj = resolver(target_id) if resolver else None
        if obj is None:
            raise ValidationError(_("العنصر غير موجود."))
        return Report.objects.create(
            reporter=reporter, target_type=target_type, target_id=target_id,
            target_label=str(obj)[:200], target_url=obj.get_absolute_url(),
            reason=reason, details=details,
        )


class ReviewService:
    @staticmethod
    def create(*, project, reviewer, rating, comment=""):
        if project.owner_id != reviewer.id or not project.freelancer_id:
            raise PermissionDenied
        if project.status != "completed":
            raise ValidationError(_("يمكن التقييم بعد اكتمال المشروع فقط."))
        if Review.objects.filter(project=project, reviewer=reviewer).exists():
            raise ValidationError(_("لقد قيّمت هذا المشروع مسبقاً."))
        return Review.objects.create(project=project, reviewer=reviewer, reviewee=project.freelancer,
                                     rating=rating, comment=comment)
