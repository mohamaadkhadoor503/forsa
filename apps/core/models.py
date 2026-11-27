from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Abstract base adding creation / modification timestamps."""

    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("آخر تحديث"), auto_now=True)

    class Meta:
        abstract = True


class SiteSettings(models.Model):
    """Singleton holding platform-wide editable settings."""

    site_name = models.CharField(_("اسم المنصة"), max_length=80, default="فرصة")
    tagline = models.CharField(_("الشعار النصي"), max_length=200, blank=True,
                               default="نربط المواهب بالفرص ونصنع مستقبلاً أفضل")
    about = models.TextField(_("نبذة"), blank=True,
                             default="منصة عربية تجمع الباحثين عن عمل والمستقلين بالشركات وأصحاب المشاريع في مكان واحد.")
    contact_email = models.EmailField(_("البريد الإلكتروني للتواصل"), blank=True, default="")
    contact_phone = models.CharField(_("رقم الهاتف"), max_length=40, blank=True)
    address = models.CharField(_("العنوان"), max_length=200, blank=True)
    twitter_url = models.URLField(_("رابط X / تويتر"), blank=True)
    linkedin_url = models.URLField(_("رابط لينكدإن"), blank=True)
    instagram_url = models.URLField(_("رابط إنستغرام"), blank=True)
    facebook_url = models.URLField(_("رابط فيسبوك"), blank=True)
    allow_registration = models.BooleanField(_("السماح بالتسجيل"), default=True)
    require_job_approval = models.BooleanField(_("مراجعة الوظائف قبل النشر"), default=False)

    class Meta:
        verbose_name = _("إعدادات المنصة")
        verbose_name_plural = _("إعدادات المنصة")

    def __str__(self):
        return str(self.site_name)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def social_links(self):
        return [
            (name, url) for name, url in (
                ("x", self.twitter_url), ("linkedin", self.linkedin_url),
                ("instagram", self.instagram_url), ("facebook", self.facebook_url),
            ) if url
        ]


class FAQ(models.Model):
    question = models.CharField(_("السؤال"), max_length=255)
    answer = models.TextField(_("الإجابة"))
    question_en = models.CharField(_("السؤال (إنجليزي)"), max_length=255, blank=True)
    answer_en = models.TextField(_("الإجابة (إنجليزي)"), blank=True)
    order = models.PositiveSmallIntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("مفعّل"), default=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = _("سؤال شائع")
        verbose_name_plural = _("الأسئلة الشائعة")

    def __str__(self):
        return self.question


class ContactMessage(TimeStampedModel):
    name = models.CharField(_("الاسم"), max_length=120)
    email = models.EmailField(_("البريد الإلكتروني"))
    subject = models.CharField(_("الموضوع"), max_length=200)
    message = models.TextField(_("الرسالة"))
    is_handled = models.BooleanField(_("تمت المعالجة"), default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("رسالة تواصل")
        verbose_name_plural = _("رسائل التواصل")

    def __str__(self):
        return f"{self.name} — {self.subject}"
