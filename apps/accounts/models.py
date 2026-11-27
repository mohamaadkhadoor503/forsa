from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        extra.setdefault("username", email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True)
        extra.setdefault("role", User.Role.ADMIN)
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Platform user. Logs in with e-mail; ``role`` decides the dashboard."""

    class Role(models.TextChoices):
        SEEKER = "seeker", _("باحث عن عمل / مستقل")
        EMPLOYER = "employer", _("صاحب عمل / شركة")
        ADMIN = "admin", _("مدير المنصة")

    email = models.EmailField(_("البريد الإلكتروني"), unique=True)
    username = models.CharField(_("اسم المستخدم"), max_length=150, unique=True)
    role = models.CharField(_("نوع الحساب"), max_length=12, choices=Role.choices, default=Role.SEEKER, db_index=True)
    avatar = models.ImageField(_("الصورة الشخصية"), upload_to="avatars/%Y/%m/", blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=30, blank=True)
    preferred_language = models.CharField(_("اللغة المفضلة"), max_length=5, default="ar")
    email_notifications = models.BooleanField(_("إشعارات البريد الإلكتروني"), default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمون")

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.get_full_name() or self.email.split("@")[0]

    @property
    def is_seeker(self):
        return self.role == self.Role.SEEKER

    @property
    def is_employer(self):
        return self.role == self.Role.EMPLOYER
