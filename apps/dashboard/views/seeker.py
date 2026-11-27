from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import ListView, TemplateView, UpdateView

from apps.applications.models import Application
from apps.core.mixins import SeekerRequiredMixin
from apps.jobs.models import SavedJob
from apps.jobs.services.recommendations import RecommendationService
from apps.projects.models import Proposal
from apps.talents.forms import CVForm, EducationForm, ExperienceForm, PortfolioItemForm, SeekerProfileForm
from apps.talents.models import Education, Experience, PortfolioItem, SeekerProfile
from apps.talents.services.profile_completion import ProfileCompletionCalculator


class SeekerProfileMixin(SeekerRequiredMixin):
    def get_profile(self):
        if not hasattr(self, "_profile"):
            self._profile, _created = SeekerProfile.objects.get_or_create(user=self.request.user)
        return self._profile

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["profile"] = self.get_profile()
        return ctx


class SeekerHomeView(SeekerProfileMixin, TemplateView):
    template_name = "dashboard/seeker/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user, profile = self.request.user, self.get_profile()
        apps = Application.objects.filter(applicant=user)
        counts = dict(apps.values_list("status").annotate(n=Count("id")))
        ctx.update(
            completion=ProfileCompletionCalculator().evaluate(profile),
            applications=apps.select_related("job__company")[:5],
            app_total=apps.count(),
            app_interviews=counts.get("interview", 0) + counts.get("offered", 0),
            app_hired=counts.get("hired", 0),
            proposals_total=Proposal.objects.filter(freelancer=user).count(),
            saved_total=SavedJob.objects.filter(user=user).count(),
            recommended=RecommendationService().for_profile(profile, 4),
        )
        return ctx


class SeekerProfileEditView(SeekerProfileMixin, UpdateView):
    template_name = "dashboard/seeker/profile.html"
    form_class = SeekerProfileForm
    success_url = reverse_lazy("dashboard:seeker_profile")

    def get_object(self, queryset=None):
        return self.get_profile()

    def get_initial(self):
        return {"skills": self.get_profile().skills.all()}

    def form_valid(self, form):
        messages.success(self.request, _("تم حفظ ملفك المهني."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["completion"] = ProfileCompletionCalculator().evaluate(self.get_profile())
        return ctx


class SeekerCVView(SeekerProfileMixin, UpdateView):
    template_name = "dashboard/seeker/cv.html"
    form_class = CVForm
    success_url = reverse_lazy("dashboard:seeker_cv")

    def get_object(self, queryset=None):
        return self.get_profile()

    def form_valid(self, form):
        messages.success(self.request, _("تم رفع السيرة الذاتية."))
        return super().form_valid(form)


class InlineCollectionView(SeekerProfileMixin, TemplateView):
    """List + add form for a profile-owned collection (portfolio, experience...)."""

    model = None
    form_class = None
    template_name = ""
    url_name = ""
    success_message = ""

    def get_items(self):
        return self.model.objects.filter(profile=self.get_profile())

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("form", self.form_class())
        ctx["items"] = self.get_items()
        return ctx

    def post(self, request):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.profile = self.get_profile()
            obj.save()
            messages.success(request, self.success_message)
            return redirect(self.url_name)
        return self.render_to_response(self.get_context_data(form=form))


class PortfolioView(InlineCollectionView):
    model = PortfolioItem
    form_class = PortfolioItemForm
    template_name = "dashboard/seeker/portfolio.html"
    url_name = "dashboard:seeker_portfolio"
    success_message = _("تمت إضافة العمل إلى معرضك.")


class ExperienceView(InlineCollectionView):
    model = Experience
    form_class = ExperienceForm
    template_name = "dashboard/seeker/experience.html"
    url_name = "dashboard:seeker_experience"
    success_message = _("تمت إضافة الخبرة.")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("edu_form", EducationForm())
        ctx["educations"] = Education.objects.filter(profile=self.get_profile())
        return ctx

    def post(self, request):
        if "education" in request.POST:
            form = EducationForm(request.POST)
            if form.is_valid():
                obj = form.save(commit=False)
                obj.profile = self.get_profile()
                obj.save()
                messages.success(request, _("تمت إضافة المؤهل."))
                return redirect(self.url_name)
            return self.render_to_response(self.get_context_data(edu_form=form))
        return super().post(request)


DELETABLE = {"portfolio": PortfolioItem, "experience": Experience, "education": Education}


class DeleteProfileItemView(SeekerProfileMixin, View):
    def post(self, request, kind, pk):
        model = DELETABLE.get(kind)
        if model is None:
            return redirect("dashboard:seeker_home")
        get_object_or_404(model, pk=pk, profile=self.get_profile()).delete()
        messages.info(request, _("تم الحذف."))
        return redirect("dashboard:seeker_portfolio" if kind == "portfolio" else "dashboard:seeker_experience")


class RecommendedJobsView(SeekerProfileMixin, TemplateView):
    template_name = "dashboard/seeker/recommended.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["jobs"] = RecommendationService().for_profile(self.get_profile(), 18)
        ctx["saved_ids"] = set(SavedJob.objects.filter(user=self.request.user).values_list("job_id", flat=True))
        return ctx


class SeekerApplicationsView(SeekerRequiredMixin, ListView):
    template_name = "dashboard/seeker/applications.html"
    context_object_name = "applications"
    paginate_by = 10

    def get_queryset(self):
        qs = Application.objects.filter(applicant=self.request.user).select_related("job__company").prefetch_related("events")
        status = self.request.GET.get("status")
        if status in Application.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Application.Status.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        return ctx


class SeekerProposalsView(SeekerRequiredMixin, ListView):
    template_name = "dashboard/seeker/proposals.html"
    context_object_name = "proposals"
    paginate_by = 10

    def get_queryset(self):
        return Proposal.objects.filter(freelancer=self.request.user).select_related("project", "project__owner")


class SavedJobsView(SeekerRequiredMixin, ListView):
    template_name = "dashboard/seeker/saved.html"
    context_object_name = "saved"
    paginate_by = 12

    def get_queryset(self):
        return SavedJob.objects.filter(user=self.request.user).select_related("job__company", "job__category").prefetch_related("job__skills")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["saved_ids"] = {s.job_id for s in ctx["saved"]}
        return ctx
