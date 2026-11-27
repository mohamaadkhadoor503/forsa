from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation


class ArabicFirstLocaleMiddleware(LocaleMiddleware):
    """Arabic by default; only an explicit user choice (language cookie) switches language.

    Django's stock middleware would follow the browser's Accept-Language header,
    which would show English to most visitors of an Arabic-first platform.
    """

    def process_request(self, request):
        chosen = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        supported = {code for code, _name in settings.LANGUAGES}
        language = chosen if chosen in supported else settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
