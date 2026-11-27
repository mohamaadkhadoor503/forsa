from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.applications.models import Application
from apps.applications.services.applications import ApplicationService
from apps.companies.forms import CompanyForm
from apps.companies.models import Company, FavoriteTalent
from apps.core.mixins import EmployerRequiredMixin
from apps.core.models import SiteSettings
from apps.core.services.stats import invalidate_stats
from apps.jobs.forms import JobForm
from apps.jobs.models import Job
from apps.projects.forms import ProjectForm
from apps.projects.models import Project, Proposal


class CompanyMixin(EmployerRequiredMixin):
    def get_company(self):
        if not hasattr(self, "_company"):
            user = self.request.user
            self._company, _c = Company.objects.get_or_create(
                owner=user, defaults={"name": user.display_name, "slug": Company.unique_slug(user.display_name)})
        return self._company

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["company"] = self.get_company()
        return ctx


class EmployerHomeView(CompanyMixin, TemplateView):
    template_name = "dashboard/employer/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        company = self.get_company()
        jobs = Job.objects.filter(company=company)
        apps = Application.objects.filter(job__company=company)
        ctx.update(
            jobs_active=jobs.filter(status=Job.Status.PUBLISHED).count(),
            jobs_total=jobs.count(),
            apps_total=apps.count(),
            apps_new=apps.filter(status=Application.Status.SUBMITTED).count(),
            hired=apps.filter(status=Application.Status.HIRED).count(),
            projects_open=Project.objects.filter(owner=self.request.user, status="open").count(),
            proposals_new=Proposal.objects.filter(project__owner=self.request.user, status="pending").count(),
            recent_apps=apps.select_related("job", "applicant").order_by("-created_at")[:6],
            top_jobs=jobs.annotate(n=Count("applications")).order_by("-n", "-created_at")[:5],
            pipeline=[(label, apps.filter(status=val).count(), val) for val, label in Application.Status.choices
                      if val != "withdrawn"],
        )
        return ctx


class CompanyEditView(CompanyMixin, UpdateView):
    template_name = "dashboard/employer/company.html"
    form_class = CompanyForm
    success_url = reverse_lazy("dashboard:employer_company")

    def get_object(self, queryset=None):
        return self.get_company()

    def form_valid(self, form):
        messages.success(self.request, _("تم تحديث ملف الشركة."))
        return super().form_valid(form)


class EmployerJobsView(CompanyMixin, ListView):
    template_name = "dashboard/employer/jobs.html"
    context_object_name = "jobs"
    paginate_by = 15

    def get_queryset(self):
        return Job.objects.filter(company=self.get_company()).select_related("category").annotate(
            apps_count=Count("applications", distinct=True),
            new_count=Count("applications", filter=Q(applications__status="submitted"), distinct=True),
        )


class JobFormMixin(CompanyMixin):
    model = Job
    form_class = JobForm
    template_name = "dashboard/employer/job_form.html"
    success_url = reverse_lazy("dashboard:employer_jobs")

    def form_valid(self, form):
        form.instance.company = self.get_company()
        form.instance.posted_by = self.request.user
        if form.instance.status == Job.Status.PUBLISHED and SiteSettings.load().require_job_approval:
            form.instance.status = Job.Status.PENDING
            messages.info(self.request, _("ستُنشر الوظيفة بعد مراجعة الإدارة."))
        response = super().form_valid(form)
        invalidate_stats()
        messages.success(self.request, _("تم حفظ الوظيفة بنجاح."))
        return response


class JobCreateView(JobFormMixin, CreateView):
    pass


class JobUpdateView(JobFormMixin, UpdateView):
    def get_queryset(self):
        return Job.objects.filter(company=self.get_company())

    def get_initial(self):
        return {"skills": self.object.skills.all()}


class JobApplicationsView(CompanyMixin, ListView):
    """Applications for one job (pk) or for all company jobs."""

    template_name = "dashboard/employer/applications.html"
    context_object_name = "applications"
    paginate_by = 15

    def get_queryset(self):
        qs = Application.objects.filter(job__company=self.get_company()).select_related(
            "job", "applicant", "applicant__profile").prefetch_related("events")
        self.job = None
        if "pk" in self.kwargs:
            self.job = get_object_or_404(Job, pk=self.kwargs["pk"], company=self.get_company())
            qs = qs.filter(job=self.job)
        status = self.request.GET.get("status")
        if status in Application.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["job"] = self.job
        ctx["statuses"] = Application.Status.choices
        ctx["current_status"] = self.request.GET.get("status", "")
        ctx["transitions"] = {a.pk: ApplicationService.allowed_transitions(a) for a in ctx["applications"]}
        return ctx


class EmployerProjectsView(EmployerRequiredMixin, ListView):
    template_name = "dashboard/employer/projects.html"
    context_object_name = "projects"
    paginate_by = 15

    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user).select_related("category", "freelancer").annotate(
            proposals_count=Count("proposals", distinct=True),
            pending_count=Count("proposals", filter=Q(proposals__status="pending"), distinct=True),
        )


class ProjectFormMixin(EmployerRequiredMixin):
    model = Project
    form_class = ProjectForm
    template_name = "dashboard/employer/project_form.html"
    success_url = reverse_lazy("dashboard:employer_projects")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, _("تم حفظ المشروع بنجاح."))
        return super().form_valid(form)


class ProjectCreateView(ProjectFormMixin, CreateView):
    pass


class ProjectUpdateView(ProjectFormMixin, UpdateView):
    def get_queryset(self):
        return Project.objects.filter(owner=self.request.user, status=Project.Status.OPEN)

    def get_initial(self):
        return {"skills": self.object.skills.all()}


class ProjectProposalsView(EmployerRequiredMixin, ListView):
    template_name = "dashboard/employer/proposals.html"
    context_object_name = "proposals"

    def get_queryset(self):
        self.project = get_object_or_404(Project, pk=self.kwargs["pk"], owner=self.request.user)
        return self.project.proposals.select_related("freelancer", "freelancer__profile").order_by("bid_amount")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["project"] = self.project
        return ctx


class FavoritesView(EmployerRequiredMixin, ListView):
    template_name = "dashboard/employer/favorites.html"
    context_object_name = "favorites"

    def get_queryset(self):
        return FavoriteTalent.objects.filter(employer=self.request.user).select_related(
            "profile__user", "profile__specialization").prefetch_related("profile__skills")
