from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Company(TimeStampedModel):
    class Size(models.TextChoices):
        S1 = "1-10", _("1 - 10 موظفين")
        S2 = "11-50", _("11 - 50 موظفاً")
        S3 = "51-200", _("51 - 200 موظف")
        S4 = "201-1000", _("201 - 1000 موظف")
        S5 = "1000+", _("أكثر من 1000")

    owner = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company")
    name = models.CharField(_("اسم الشركة"), max_length=120)
    slug = models.SlugField(max_length=140, unique=True, allow_unicode=True)
    logo = models.ImageField(_("الشعار"), upload_to="logos/%Y/", blank=True)
    cover = models.ImageField(_("صورة الغلاف"), upload_to="covers/%Y/", blank=True)
    tagline = models.CharField(_("نبذة قصيرة"), max_length=160, blank=True)
    description = models.TextField(_("عن الشركة"), blank=True)
    industry = models.ForeignKey("jobs.Category", on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("المجال"))
    size = models.CharField(_("حجم الشركة"), max_length=10, choices=Size.choices, blank=True)
    website = models.URLField(_("الموقع الإلكتروني"), blank=True)
    location = models.CharField(_("المقر"), max_length=120, blank=True)
    founded_year = models.PositiveSmallIntegerField(_("سنة التأسيس"), null=True, blank=True)
    linkedin = models.URLField(_("لينكدإن"), blank=True)
    is_verified = models.BooleanField(_("موثّقة"), default=False)
    is_featured = models.BooleanField(_("شريك معتمد يظهر في الرئيسية"), default=False,
                                      help_text=_("فعّلها فقط للشركات المتعاونة فعلياً مع المنصة"))

    class Meta:
        ordering = ["-is_verified", "name"]
        verbose_name = _("شركة")
        verbose_name_plural = _("الشركات")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("companies:detail", args=[self.slug])

    @classmethod
    def unique_slug(cls, name):
        from apps.jobs.models import unique_slug
        return unique_slug(cls, name, 140)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.unique_slug(self.name)
        super().save(*args, **kwargs)


class FavoriteTalent(models.Model):
    """Employer's shortlist of candidates."""

    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_talents")
    profile = models.ForeignKey("talents.SeekerProfile", on_delete=models.CASCADE, related_name="favorited_by")
    note = models.CharField(_("ملاحظة"), max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("employer", "profile")
        ordering = ["-created_at"]
        verbose_name = _("مرشح مفضل")
        verbose_name_plural = _("المرشحون المفضلون")
