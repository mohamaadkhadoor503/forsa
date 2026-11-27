from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import translation
from django.utils.translation import gettext as _
from django.views import View

from apps.accounts.forms import AccountSettingsForm, StyledPasswordChangeForm


class DashboardHomeRedirect(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        if user.is_staff:
            return redirect("dashboard:admin_home")
        if user.is_employer:
            return redirect("dashboard:employer_home")
        return redirect("dashboard:seeker_home")


class AccountSettingsView(LoginRequiredMixin, View):
    template_name = "dashboard/settings.html"

    def get(self, request):
        return self._render(AccountSettingsForm(instance=request.user), StyledPasswordChangeForm(request.user))

    def post(self, request):
        account_form = AccountSettingsForm(instance=request.user)
        password_form = StyledPasswordChangeForm(request.user)
        if "save_account" in request.POST:
            account_form = AccountSettingsForm(request.POST, request.FILES, instance=request.user)
            if account_form.is_valid():
                user = account_form.save()
                messages.success(request, _("تم حفظ إعدادات الحساب."))
                response = redirect("dashboard:settings")
                response.set_cookie("django_language", user.preferred_language, max_age=365 * 24 * 3600)
                translation.activate(user.preferred_language)
                return response
        elif "change_password" in request.POST:
            password_form = StyledPasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, _("تم تغيير كلمة المرور."))
                return redirect("dashboard:settings")
        return self._render(account_form, password_form)

    def _render(self, account_form, password_form):
        return render(self.request, self.template_name, {"account_form": account_form, "password_form": password_form})
