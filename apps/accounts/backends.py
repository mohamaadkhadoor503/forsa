from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Authenticate with a case-insensitive e-mail address."""

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        User = get_user_model()
        login = (email or username or "").strip().lower()
        if not login or not password:
            return None
        try:
            user = User.objects.get(email__iexact=login)
        except User.DoesNotExist:
            User().set_password(password)  # mitigate timing attacks
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
