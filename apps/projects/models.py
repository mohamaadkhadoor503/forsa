from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.jobs.models import ExperienceLevel, unique_slug


class Project(TimeStampedModel):
    class Status(models.TextChoices):
        OPEN = "open", _("مفتوح لاستقبال العروض")
        IN_PROGRESS = "in_progress", _("قيد التنفيذ")
        COMPLETED = "completed", _("مكتمل")
        CANCELLED = "cancelled", _("ملغى")

    class BudgetType(models.TextChoices):
        FIXED = "fixed", _("سعر ثابت")
        HOURLY = "hourly", _("بالساعة")

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(_("عنوان المشروع"), max_length=160)
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)
    category = models.ForeignKey("jobs.Category", on_delete=models.PROTECT, related_name="projects", verbose_name=_("التخصص"))
    description = models.TextField(_("وصف المشروع"))
    deliverables = models.TextField(_("المخرجات المطلوبة"), blank=True, help_text=_("سطر لكل مخرج"))
    budget_type = models.CharField(_("نوع الميزانية"), max_length=8, choices=BudgetType.choices, default=BudgetType.FIXED)
    budget_min = models.PositiveIntegerField(_("الميزانية من ($)"))
    budget_max = models.PositiveIntegerField(_("الميزانية إلى ($)"))
    duration_days = models.PositiveSmallIntegerField(_("مدة التنفيذ (أيام)"))
    experience_level = models.CharField(_("مستوى الخبرة"), max_length=10, choices=ExperienceLevel.choices, default=ExperienceLevel.MID)
    skills = models.ManyToManyField("jobs.Skill", blank=True, related_name="projects", verbose_name=_("المهارات المطلوبة"))
    status = models.CharField(_("الحالة"), max_length=12, choices=Status.choices, default=Status.OPEN, db_index=True)
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="awarded_projects", verbose_name=_("المستقل المنفذ"))

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("مشروع")
        verbose_name_plural = _("المشاريع")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Project, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.slug])

    @property
    def budget_display(self):
        suffix = _("/ساعة") if self.budget_type == self.BudgetType.HOURLY else ""
        return f"${self.budget_min:,} – ${self.budget_max:,}{suffix}"

    @property
    def owner_company(self):
        return getattr(self.owner, "company", None)


class Proposal(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", _("بانتظار الرد")
        SHORTLISTED = "shortlisted", _("في القائمة المختصرة")
        ACCEPTED = "accepted", _("مقبول")
        REJECTED = "rejected", _("مرفوض")
        WITHDRAWN = "withdrawn", _("مسحوب")

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="proposals")
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="proposals")
    cover_letter = models.TextField(_("تفاصيل العرض"))
    bid_amount = models.PositiveIntegerField(_("قيمة العرض ($)"))
    delivery_days = models.PositiveSmallIntegerField(_("مدة التسليم (أيام)"))
    status = models.CharField(_("الحالة"), max_length=12, choices=Status.choices, default=Status.PENDING, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("project", "freelancer")
        verbose_name = _("عرض")
        verbose_name_plural = _("العروض")

    def __str__(self):
        return f"{self.freelancer} → {self.project}"
