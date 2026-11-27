from django.utils.translation import get_language_bidi

from .models import SiteSettings


def site(request):
    return {
        "site_settings": SiteSettings.load(),
        "is_rtl": get_language_bidi(),
    }
