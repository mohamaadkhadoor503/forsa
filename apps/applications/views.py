from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import FormView

from apps.core.mixins import EmployerRequiredMixin, SeekerRequiredMixin
from apps.jobs.models import Job

from .forms import ApplicationForm, StatusChangeForm
from .models import Application
from .services.applications import ApplicationService


class ApplyView(SeekerRequiredMixin, FormView):
    template_name = "applications/apply.html"
    form_class = ApplicationForm

    def dispatch(self, request, *args, **kwargs):
        self.job = get_object_or_404(Job.objects.with_relations(), slug=kwargs["slug"])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["job"] = self.job
        ctx["profile"] = getattr(self.request.user, "profile", None)
        return ctx

    def form_valid(self, form):
        try:
            ApplicationService().apply(
                job=self.job, applicant=self.request.user,
                cover_letter=form.cleaned_data["cover_letter"],
                cv=form.cleaned_data.get("cv"),
                expected_salary=form.cleaned_data.get("expected_salary"),
            )
        except ValidationError as exc:
            messages.error(self.request, exc.messages[0])
            return redirect(self.job.get_absolute_url())
        messages.success(self.request, _("تم إرسال طلبك بنجاح! سنُعلمك بأي تحديث."))
        return redirect("dashboard:seeker_applications")


class WithdrawApplicationView(SeekerRequiredMixin, View):
    def post(self, request, pk):
        app = get_object_or_404(Application, pk=pk, applicant=request.user)
        try:
            ApplicationService().withdraw(app, request.user)
            messages.info(request, _("تم سحب الطلب."))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        return redirect("dashboard:seeker_applications")


class ChangeApplicationStatusView(EmployerRequiredMixin, View):
    def post(self, request, pk):
        app = get_object_or_404(Application.objects.select_related("job__company"), pk=pk,
                                job__company__owner=request.user)
        form = StatusChangeForm(request.POST)
        if form.is_valid():
            try:
                ApplicationService().change_status(app, form.cleaned_data["status"], request.user, form.cleaned_data["note"])
                messages.success(request, _("تم تحديث حالة الطلب."))
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
        return redirect(request.POST.get("next") or "dashboard:employer_applications")
