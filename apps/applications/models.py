from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Application(TimeStampedModel):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", _("تم التقديم")
        REVIEWING = "reviewing", _("قيد المراجعة")
        SHORTLISTED = "shortlisted", _("في القائمة المختصرة")
        INTERVIEW = "interview", _("مقابلة")
        OFFERED = "offered", _("عرض وظيفي")
        HIRED = "hired", _("تم التوظيف")
        REJECTED = "rejected", _("مرفوض")
        WITHDRAWN = "withdrawn", _("تم السحب")

    # The "happy path" displayed as a progress timeline.
    PIPELINE = [Status.SUBMITTED, Status.REVIEWING, Status.SHORTLISTED, Status.INTERVIEW, Status.OFFERED, Status.HIRED]
    FINAL = {Status.HIRED, Status.REJECTED, Status.WITHDRAWN}

    job = models.ForeignKey("jobs.Job", on_delete=models.CASCADE, related_name="applications", verbose_name=_("الوظيفة"))
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    cover_letter = models.TextField(_("رسالة التقديم"))
    cv = models.FileField(_("السيرة الذاتية"), upload_to="applications/%Y/", blank=True,
                          validators=[FileExtensionValidator(["pdf", "doc", "docx"])])
    expected_salary = models.PositiveIntegerField(_("الراتب المتوقع"), null=True, blank=True)
    status = models.CharField(_("الحالة"), max_length=12, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    employer_note = models.TextField(_("ملاحظات داخلية"), blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("job", "applicant")
        verbose_name = _("طلب توظيف")
        verbose_name_plural = _("طلبات التوظيف")

    def __str__(self):
        return f"{self.applicant} → {self.job}"

    @property
    def is_final(self):
        return self.status in self.FINAL

    @property
    def cv_file(self):
        if self.cv:
            return self.cv
        profile = getattr(self.applicant, "profile", None)
        return profile.cv if profile and profile.cv else None

    def pipeline_steps(self):
        """Steps for the timeline UI: (status, label, state) where state ∈ done/current/todo/failed."""
        steps = []
        try:
            idx = self.PIPELINE.index(self.status)
        except ValueError:
            idx = -1
        history = {e.status for e in self.events.all()}
        for i, st in enumerate(self.PIPELINE):
            if idx >= 0:
                state = "done" if i < idx else "current" if i == idx else "todo"
            else:
                state = "done" if st in history else "todo"
            steps.append((st, self.Status(st).label, state))
        if self.status in (self.Status.REJECTED, self.Status.WITHDRAWN):
            steps.append((self.status, self.get_status_display(), "failed"))
        return steps


class ApplicationEvent(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=12, choices=Application.Status.choices)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
