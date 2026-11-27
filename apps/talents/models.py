from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.jobs.models import ExperienceLevel


class SeekerProfile(TimeStampedModel):
    class Availability(models.TextChoices):
        AVAILABLE = "available", _("متاح للعمل")
        OPEN = "open", _("منفتح على الفرص")
        BUSY = "busy", _("غير متاح حالياً")

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    headline = models.CharField(_("المسمى المهني"), max_length=120, blank=True)
    bio = models.TextField(_("نبذة عني"), blank=True)
    specialization = models.ForeignKey("jobs.Category", on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("التخصص"))
    location = models.CharField(_("الموقع"), max_length=120, blank=True)
    years_experience = models.PositiveSmallIntegerField(_("سنوات الخبرة"), default=0)
    experience_level = models.CharField(_("مستوى الخبرة"), max_length=10, choices=ExperienceLevel.choices, default=ExperienceLevel.ENTRY)
    availability = models.CharField(_("حالة التوفر"), max_length=10, choices=Availability.choices, default=Availability.AVAILABLE)
    hourly_rate = models.PositiveIntegerField(_("السعر بالساعة ($)"), null=True, blank=True)
    skills = models.ManyToManyField("jobs.Skill", blank=True, related_name="profiles", verbose_name=_("المهارات"))
    cv = models.FileField(_("السيرة الذاتية (PDF)"), upload_to="cvs/%Y/", blank=True,
                          validators=[FileExtensionValidator(["pdf", "doc", "docx"])])
    website = models.URLField(_("الموقع الشخصي"), blank=True)
    github = models.URLField(_("GitHub"), blank=True)
    linkedin = models.URLField(_("LinkedIn"), blank=True)
    is_public = models.BooleanField(_("ملف عام يظهر في البحث"), default=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = _("ملف باحث عن عمل")
        verbose_name_plural = _("ملفات الباحثين عن عمل")

    def __str__(self):
        return self.user.display_name

    def get_absolute_url(self):
        return reverse("talents:detail", args=[self.pk])


class Experience(models.Model):
    profile = models.ForeignKey(SeekerProfile, on_delete=models.CASCADE, related_name="experiences")
    title = models.CharField(_("المسمى"), max_length=120)
    company = models.CharField(_("الجهة"), max_length=120)
    start_date = models.DateField(_("تاريخ البداية"))
    end_date = models.DateField(_("تاريخ النهاية"), null=True, blank=True)
    is_current = models.BooleanField(_("أعمل هنا حالياً"), default=False)
    description = models.TextField(_("الوصف"), blank=True)

    class Meta:
        ordering = ["-is_current", "-start_date"]
        verbose_name = _("خبرة")
        verbose_name_plural = _("الخبرات")

    def __str__(self):
        return f"{self.title} @ {self.company}"


class Education(models.Model):
    profile = models.ForeignKey(SeekerProfile, on_delete=models.CASCADE, related_name="educations")
    degree = models.CharField(_("الدرجة / الشهادة"), max_length=120)
    institution = models.CharField(_("المؤسسة التعليمية"), max_length=150)
    start_year = models.PositiveSmallIntegerField(_("سنة البداية"))
    end_year = models.PositiveSmallIntegerField(_("سنة التخرج"), null=True, blank=True)

    class Meta:
        ordering = ["-start_year"]
        verbose_name = _("تعليم")
        verbose_name_plural = _("التعليم")

    def __str__(self):
        return self.degree


class PortfolioItem(TimeStampedModel):
    profile = models.ForeignKey(SeekerProfile, on_delete=models.CASCADE, related_name="portfolio")
    title = models.CharField(_("عنوان العمل"), max_length=120)
    description = models.TextField(_("الوصف"), blank=True)
    image = models.ImageField(_("صورة"), upload_to="portfolio/%Y/", blank=True)
    url = models.URLField(_("رابط"), blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("عمل سابق")
        verbose_name_plural = _("معرض الأعمال")

    def __str__(self):
        return self.title
