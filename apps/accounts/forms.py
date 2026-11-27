from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _

from .models import User


class LoginForm(forms.Form):
    email = forms.EmailField(label=_("البريد الإلكتروني"), widget=forms.EmailInput(attrs={"autocomplete": "email", "autofocus": True}))
    password = forms.CharField(label=_("كلمة المرور"), widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}))
    remember = forms.BooleanField(label=_("تذكرني"), required=False, initial=True)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        self.user = authenticate(self.request, email=data["email"], password=data["password"])
        if self.user is None:
            raise forms.ValidationError(_("البريد الإلكتروني أو كلمة المرور غير صحيحة."))
        return data


class SignupForm(forms.Form):
    first_name = forms.CharField(label=_("الاسم الأول"), max_length=60)
    last_name = forms.CharField(label=_("اسم العائلة"), max_length=60)
    email = forms.EmailField(label=_("البريد الإلكتروني"), widget=forms.EmailInput(attrs={"autocomplete": "email"}))
    company_name = forms.CharField(label=_("اسم الشركة / الجهة"), max_length=120, required=False)
    password1 = forms.CharField(label=_("كلمة المرور"), widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "data-strength": "1"}))
    password2 = forms.CharField(label=_("تأكيد كلمة المرور"), widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}))
    terms = forms.BooleanField(label=_("أوافق على الشروط والأحكام وسياسة الخصوصية"))

    def __init__(self, *args, role=User.Role.SEEKER, **kwargs):
        self.role = role
        super().__init__(*args, **kwargs)
        if role != User.Role.EMPLOYER:
            del self.fields["company_name"]
        else:
            self.fields["company_name"].required = True

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("هذا البريد مسجل مسبقاً."))
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get("password1"), data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", _("كلمتا المرور غير متطابقتين."))
        if p1:
            try:
                password_validation.validate_password(
                    p1, User(email=data.get("email", ""), first_name=data.get("first_name", "")))
            except forms.ValidationError as exc:
                self.add_error("password1", exc)
        return data


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone", "avatar", "preferred_language", "email_notifications"]
        widgets = {"preferred_language": forms.Select(choices=[("ar", "العربية"), ("en", "English")])}

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("هذا البريد مستخدم من حساب آخر."))
        return email


class StyledPasswordChangeForm(PasswordChangeForm):
    pass


class StyledPasswordResetForm(PasswordResetForm):
    pass


class StyledSetPasswordForm(SetPasswordForm):
    pass
