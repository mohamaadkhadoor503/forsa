from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import views as auth_views
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from apps.core.models import SiteSettings

from .forms import LoginForm, SignupForm, StyledPasswordResetForm, StyledSetPasswordForm
from .models import User
from .services.registration import RegistrationService


class AnonymousOnlyMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)


class LoginView(AnonymousOnlyMixin, FormView):
    template_name = "accounts/login.html"
    form_class = LoginForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.user)
        if not form.cleaned_data.get("remember"):
            self.request.session.set_expiry(0)
        messages.success(self.request, _("مرحباً بعودتك، %(name)s!") % {"name": form.user.display_name})
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url and url_has_allowed_host_and_scheme(next_url, {self.request.get_host()}):
            return redirect(next_url)
        return redirect("dashboard:home")


class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, _("تم تسجيل الخروج بنجاح."))
        return redirect("core:home")


class ChooseAccountTypeView(AnonymousOnlyMixin, TemplateView):
    template_name = "accounts/choose_type.html"


class SignupView(AnonymousOnlyMixin, FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    service_class = RegistrationService

    def dispatch(self, request, *args, **kwargs):
        if kwargs["role"] not in (User.Role.SEEKER, User.Role.EMPLOYER):
            raise Http404
        if not SiteSettings.load().allow_registration:
            messages.warning(request, _("التسجيل متوقف مؤقتاً."))
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["role"] = self.kwargs["role"]
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role"] = self.kwargs["role"]
        return ctx

    def form_valid(self, form):
        data = form.cleaned_data
        user = self.service_class().register(
            email=data["email"], password=data["password1"],
            first_name=data["first_name"], last_name=data["last_name"],
            role=self.kwargs["role"], company_name=data.get("company_name", ""),
        )
        login(self.request, user, backend="apps.accounts.backends.EmailBackend")
        messages.success(self.request, _("تم إنشاء حسابك بنجاح! أكمل ملفك لتبدأ."))
        return redirect("dashboard:home")


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/emails/password_reset_email.txt"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    form_class = StyledPasswordResetForm
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = StyledSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"
