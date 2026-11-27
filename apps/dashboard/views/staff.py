"""Platform administration dashboard (is_staff users)."""
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from apps.applications.models import Application
from apps.companies.models import Company
from apps.core.forms import SiteSettingsForm
from apps.core.mixins import QueryStringMixin, StaffRequiredMixin
from apps.core.models import ContactMessage, SiteSettings
from apps.core.services.stats import PlatformStatsService, invalidate_stats
from apps.jobs.models import Category, Job
from apps.projects.models import Project
from apps.reviews.models import Report, Testimonial

User = get_user_model()


def monthly_counts(qs, field="created_at", months=6):
    since = timezone.now() - timedelta(days=31 * months)
    rows = (qs.filter(**{f"{field}__gte": since}).annotate(m=TruncMonth(field))
            .values("m").annotate(n=Count("id")).order_by("m"))
    return [(r["m"].strftime("%Y-%m"), r["n"]) for r in rows if r["m"]]


class AdminHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/admin/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["stats"] = PlatformStatsService().get(use_cache=False)
        ctx["signups"] = monthly_counts(User.objects.all(), "date_joined")
        ctx["jobs_by_month"] = monthly_counts(Job.objects.all())
        ctx["apps_by_month"] = monthly_counts(Application.objects.all())
        ctx["top_categories"] = Category.objects.annotate(n=Count("jobs")).order_by("-n")[:6]
        ctx["open_reports"] = Report.objects.filter(status=Report.Status.OPEN).count()
        ctx["pending_testimonials"] = Testimonial.objects.filter(is_approved=False).count()
        ctx["pending_jobs"] = Job.objects.filter(status=Job.Status.PENDING).count()
        ctx["recent_users"] = User.objects.order_by("-date_joined")[:6]
        return ctx


class SearchListMixin(StaffRequiredMixin, QueryStringMixin):
    paginate_by = 20
    search_fields = ()

    def search(self, qs):
        q = self.request.GET.get("q", "").strip()
        if q:
            cond = Q()
            for f in self.search_fields:
                cond |= Q(**{f"{f}__icontains": q})
            qs = qs.filter(cond)
        return qs


class AdminUsersView(SearchListMixin, ListView):
    template_name = "dashboard/admin/users.html"
    context_object_name = "users"
    search_fields = ("email", "first_name", "last_name")

    def get_queryset(self):
        qs = self.search(User.objects.order_by("-date_joined"))
        role = self.request.GET.get("role")
        if role in User.Role.values:
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["roles"] = User.Role.choices
        return ctx


class AdminCompaniesView(SearchListMixin, ListView):
    template_name = "dashboard/admin/companies.html"
    context_object_name = "companies"
    search_fields = ("name", "owner__email")

    def get_queryset(self):
        return self.search(Company.objects.select_related("owner").annotate(n=Count("jobs")).order_by("-created_at"))


class AdminJobsView(SearchListMixin, ListView):
    template_name = "dashboard/admin/jobs.html"
    context_object_name = "jobs"
    search_fields = ("title", "company__name")

    def get_queryset(self):
        qs = self.search(Job.objects.select_related("company", "category").order_by("-created_at"))
        status = self.request.GET.get("status")
        if status in Job.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Job.Status.choices
        return ctx


class AdminProjectsView(SearchListMixin, ListView):
    template_name = "dashboard/admin/projects.html"
    context_object_name = "projects"
    search_fields = ("title", "owner__email")

    def get_queryset(self):
        return self.search(Project.objects.select_related("owner", "category").annotate(
            n=Count("proposals")).order_by("-created_at"))


class AdminCategoriesView(StaffRequiredMixin, ListView):
    template_name = "dashboard/admin/categories.html"
    context_object_name = "categories"

    def get_queryset(self):
        return Category.objects.annotate(jobs_n=Count("jobs", distinct=True), projects_n=Count("projects", distinct=True))


class CategoryFormMixin(StaffRequiredMixin):
    model = Category
    fields = ["name", "name_en", "slug", "icon", "color", "order", "is_active"]
    template_name = "dashboard/admin/category_form.html"
    success_url = reverse_lazy("dashboard:admin_categories")

    def form_valid(self, form):
        messages.success(self.request, _("تم حفظ التصنيف."))
        return super().form_valid(form)


class CategoryCreateView(CategoryFormMixin, CreateView):
    pass


class CategoryUpdateView(CategoryFormMixin, UpdateView):
    pass


class AdminReportsView(StaffRequiredMixin, ListView):
    template_name = "dashboard/admin/reports.html"
    context_object_name = "reports"
    paginate_by = 20

    def get_queryset(self):
        qs = Report.objects.select_related("reporter")
        status = self.request.GET.get("status")
        if status in Report.Status.values:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuses"] = Report.Status.choices
        return ctx


class AdminContentView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/admin/content.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["testimonials"] = Testimonial.objects.select_related("author")[:50]
        ctx["pending_jobs"] = Job.objects.filter(status=Job.Status.PENDING).select_related("company")
        ctx["contact_messages"] = ContactMessage.objects.all()[:30]
        return ctx


class AdminSettingsView(StaffRequiredMixin, UpdateView):
    template_name = "dashboard/admin/settings.html"
    form_class = SiteSettingsForm
    success_url = reverse_lazy("dashboard:admin_settings")

    def get_object(self, queryset=None):
        return SiteSettings.load()

    def form_valid(self, form):
        messages.success(self.request, _("تم حفظ إعدادات المنصة."))
        return super().form_valid(form)


class AdminActionView(StaffRequiredMixin, View):
    """Single endpoint for small moderation toggles. Each action is a tiny handler."""

    def _user_active(self, pk, value):
        user = get_object_or_404(User, pk=pk)
        if user.pk == self.request.user.pk:
            return _("لا يمكنك تعطيل حسابك.")
        user.is_active = value == "1"
        user.save(update_fields=["is_active"])

    def _company_verify(self, pk, value):
        Company.objects.filter(pk=pk).update(is_verified=value == "1")

    def _company_feature(self, pk, value):
        Company.objects.filter(pk=pk).update(is_featured=value == "1")

    def _job_status(self, pk, value):
        if value in Job.Status.values:
            Job.objects.filter(pk=pk).update(status=value)

    def _job_feature(self, pk, value):
        Job.objects.filter(pk=pk).update(is_featured=value == "1")

    def _project_status(self, pk, value):
        if value in Project.Status.values:
            Project.objects.filter(pk=pk).update(status=value)

    def _report_status(self, pk, value):
        if value in Report.Status.values:
            Report.objects.filter(pk=pk).update(status=value)

    def _testimonial(self, pk, value):
        if value == "delete":
            Testimonial.objects.filter(pk=pk).delete()
        else:
            Testimonial.objects.filter(pk=pk).update(is_approved=value == "1")

    def _contact_handled(self, pk, value):
        ContactMessage.objects.filter(pk=pk).update(is_handled=value == "1")

    HANDLERS = {
        "user_active": _user_active, "company_verify": _company_verify, "company_feature": _company_feature,
        "job_status": _job_status, "job_feature": _job_feature, "project_status": _project_status,
        "report_status": _report_status, "testimonial": _testimonial, "contact_handled": _contact_handled,
    }

    def post(self, request, action, pk):
        handler = self.HANDLERS.get(action)
        if handler:
            error = handler(self, pk, request.POST.get("value", ""))
            if error:
                messages.error(request, error)
            else:
                messages.success(request, _("تم تنفيذ الإجراء."))
                invalidate_stats()
        return redirect(request.POST.get("next") or "dashboard:admin_home")
