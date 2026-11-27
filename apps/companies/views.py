from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.core.filtering import ContainsFilter, ExactFilter, FilterSet, KeywordFilter
from apps.core.mixins import PartialTemplateMixin, QueryStringMixin
from apps.jobs.models import Category, Job

from .models import Company


class CompanyFilterSet(FilterSet):
    filters = [
        KeywordFilter("q", _("كلمة"), fields=("name", "tagline", "description")),
        ExactFilter("industry", _("المجال"), field="industry__slug"),
        ContainsFilter("location", _("الموقع"), field="location"),
        ExactFilter("size", _("الحجم"), field="size", choices=dict(Company.Size.choices)),
    ]
    orderings = {
        "jobs": (("-open_jobs", "name"), _("الأكثر وظائف")),
        "name": (("name",), _("الاسم")),
        "newest": (("-created_at",), _("الأحدث")),
    }
    default_ordering = "jobs"


def companies_with_counts():
    return Company.objects.select_related("industry").annotate(
        open_jobs=Count("jobs", filter=Q(jobs__status=Job.Status.PUBLISHED), distinct=True)
    )


class CompanyListView(PartialTemplateMixin, QueryStringMixin, ListView):
    template_name = "companies/list.html"
    partial_template_name = "companies/_results.html"
    context_object_name = "companies"
    paginate_by = 12

    def get_queryset(self):
        self.filterset = CompanyFilterSet(self.request.GET, companies_with_counts())
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filterset"] = self.filterset
        ctx["industries"] = Category.objects.filter(is_active=True)
        ctx["sizes"] = Company.Size.choices
        return ctx


class CompanyDetailView(DetailView):
    template_name = "companies/detail.html"
    context_object_name = "company"

    def get_queryset(self):
        return companies_with_counts()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["jobs"] = Job.objects.published().with_relations().filter(company=self.object)
        ctx["projects"] = self.object.owner.projects.filter(status="open").prefetch_related("skills")[:6]
        return ctx
