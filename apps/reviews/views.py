from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView

from apps.core.mixins import EmployerRequiredMixin
from apps.projects.models import Project

from .forms import ReportForm, ReviewForm, TestimonialForm
from .models import Testimonial
from .services import ReportService, ReviewService


def _back(request, fallback="core:home"):
    nxt = request.POST.get("next")
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
        return redirect(nxt)
    return redirect(fallback)


class SubmitReviewView(EmployerRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk, owner=request.user)
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                ReviewService.create(project=project, reviewer=request.user, **form.cleaned_data)
                messages.success(request, _("شكراً! تم نشر تقييمك."))
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
        return redirect(project.get_absolute_url())


class SubmitTestimonialView(LoginRequiredMixin, CreateView):
    model = Testimonial
    form_class = TestimonialForm
    template_name = "dashboard/testimonial_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        messages.success(self.request, _("شكراً لمشاركتك! سيظهر رأيك بعد مراجعته من الإدارة."))
        return redirect("dashboard:home")


class SubmitReportView(LoginRequiredMixin, View):
    def post(self, request, target_type, target_id):
        form = ReportForm(request.POST)
        if form.is_valid():
            try:
                ReportService.create(reporter=request.user, target_type=target_type, target_id=target_id,
                                     **form.cleaned_data)
                messages.success(request, _("تم استلام البلاغ وسيتم مراجعته. شكراً لك."))
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
        else:
            messages.error(request, _("يرجى اختيار سبب البلاغ."))
        return _back(request)
