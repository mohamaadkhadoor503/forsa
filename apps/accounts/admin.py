from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["-date_joined"]
    list_display = ["email", "first_name", "last_name", "role", "is_active", "is_staff", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        (_("البيانات الشخصية"), {"fields": ("first_name", "last_name", "phone", "avatar", "role", "preferred_language")}),
        (_("الصلاحيات"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("تواريخ"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "username", "role", "password1", "password2")}),)
