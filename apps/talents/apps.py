from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TalentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.talents"
    verbose_name = _("المواهب")
