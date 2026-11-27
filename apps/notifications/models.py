from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class Kind(models.TextChoices):
        INFO = "info", _("معلومة")
        SUCCESS = "success", _("نجاح")
        APPLICATION = "application", _("طلب توظيف")
        PROPOSAL = "proposal", _("عرض مشروع")
        MESSAGE = "message", _("رسالة")

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.INFO)
    title = models.CharField(_("العنوان"), max_length=160)
    body = models.CharField(_("النص"), max_length=300, blank=True)
    url = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("إشعار")
        verbose_name_plural = _("الإشعارات")

    def __str__(self):
        return self.title
