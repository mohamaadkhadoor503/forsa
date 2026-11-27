from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel

RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(5)]


class Review(TimeStampedModel):
    """A verified rating: only a project owner can rate the freelancer who completed it."""

    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_given")
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews_received")
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(_("التقييم"), validators=RATING_VALIDATORS)
    comment = models.TextField(_("التعليق"), blank=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("reviewer", "project")
        verbose_name = _("تقييم")
        verbose_name_plural = _("التقييمات")


class Testimonial(TimeStampedModel):
    """User opinion about the platform. Shown publicly only after admin approval."""

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="testimonials")
    role_title = models.CharField(_("المسمى / التخصص"), max_length=100)
    content = models.TextField(_("رأيك في المنصة"), max_length=600)
    rating = models.PositiveSmallIntegerField(_("التقييم"), validators=RATING_VALIDATORS, default=5)
    is_approved = models.BooleanField(_("معتمد للنشر"), default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("رأي مستخدم")
        verbose_name_plural = _("آراء المستخدمين")

    def __str__(self):
        return f"{self.author} ({self.rating}★)"


class Report(TimeStampedModel):
    class Target(models.TextChoices):
        JOB = "job", _("وظيفة")
        PROJECT = "project", _("مشروع")
        COMPANY = "company", _("شركة")
        PROFILE = "profile", _("ملف شخصي")

    class Reason(models.TextChoices):
        SPAM = "spam", _("محتوى مزعج / إعلاني")
        FRAUD = "fraud", _("احتيال أو نصب")
        OFFENSIVE = "offensive", _("محتوى مسيء")
        MISLEADING = "misleading", _("معلومات مضللة")
        OTHER = "other", _("أخرى")

    class Status(models.TextChoices):
        OPEN = "open", _("جديد")
        REVIEWING = "reviewing", _("قيد المراجعة")
        RESOLVED = "resolved", _("تم الحل")
        DISMISSED = "dismissed", _("مرفوض")

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    target_type = models.CharField(_("نوع العنصر"), max_length=10, choices=Target.choices)
    target_id = models.PositiveIntegerField()
    target_label = models.CharField(max_length=200, blank=True)
    target_url = models.CharField(max_length=300, blank=True)
    reason = models.CharField(_("السبب"), max_length=12, choices=Reason.choices)
    details = models.TextField(_("التفاصيل"), blank=True, max_length=1000)
    status = models.CharField(_("الحالة"), max_length=10, choices=Status.choices, default=Status.OPEN, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("بلاغ")
        verbose_name_plural = _("البلاغات")
