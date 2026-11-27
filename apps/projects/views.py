from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.filtering import ExactFilter, FilterSet, KeywordFilter, NumberFilter, SkillsFilter
from apps.core.mixins import EmployerRequiredMixin, PartialTemplateMixin, QueryStringMixin, SeekerRequiredMixin
from apps.jobs.models import Category, ExperienceLevel, Skill

from .forms import ProposalForm
from .models import Project, Proposal
from .services.proposals import ProjectService, ProposalService


class ProjectFilterSet(FilterSet):
    filters = [
        KeywordFilter("q", _l("كلمة"), fields=("title", "description", "skills__name")),
        ExactFilter("category", _l("التخصص"), field="category__slug"),
        ExactFilter("level", "", field="experience_level", choices=dict(ExperienceLevel.choices)),
        ExactFilter("budget_type", "", field="budget_type", choices=dict(Project.BudgetType.choices)),
        NumberFilter("budget_min", _l("ميزانية من"), field="budget_max", lookup="gte"),
        NumberFilter("budget_max", _l("ميزانية حتى"), field="budget_min", lookup="lte"),
        NumberFilter("max_days", _l("مدة حتى"), field="duration_days", lookup="lte"),
        SkillsFilter("skill", _l("مهارة")),
    ]
    orderings = {
        "newest": (("-created_at",), _l("الأحدث")),
        "budget": (("-budget_max",), _l("الأعلى ميزانية")),
        "proposals": (("proposals_count", "-created_at"), _l("الأقل عروضاً")),
    }
    default_ordering = "newest"

    @property
    def qs(self):
        return super().qs.distinct()


def projects_qs():
    return (
        Project.objects.select_related("owner", "owner__company", "category")
        .prefetch_related("skills")
        .annotate(proposals_count=Count("proposals", filter=~Q(proposals__status="withdrawn"), distinct=True))
    )


class ProjectListView(PartialTemplateMixin, QueryStringMixin, ListView):
    template_name = "projects/list.html"
    partial_template_name = "projects/_results.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        self.filterset = ProjectFilterSet(self.request.GET, projects_qs().filter(status=Project.Status.OPEN))
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            filterset=self.filterset,
            categories=Category.objects.filter(is_active=True),
            levels=ExperienceLevel.choices,
            budget_types=Project.BudgetType.choices,
            popular_skills=Skill.objects.all()[:40],
            view_mode=self.request.GET.get("view", "grid"),
        )
        return ctx


class ProjectDetailView(DetailView):
    template_name = "projects/detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return projects_qs()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        project = self.object
        ctx["my_proposal"] = None
        ctx["form"] = None
        if user.is_authenticated and user.is_seeker:
            ctx["my_proposal"] = project.proposals.filter(freelancer=user).first()
            if not ctx["my_proposal"] and project.status == Project.Status.OPEN:
                ctx["form"] = ProposalForm(initial={"bid_amount": project.budget_min, "delivery_days": project.duration_days})
        ctx["is_owner"] = user.is_authenticated and project.owner_id == user.id
        ctx["can_review"] = (
            ctx["is_owner"] and project.status == Project.Status.COMPLETED and project.freelancer_id
            and not project.reviews.filter(reviewer=user).exists()
        )
        ctx["similar"] = projects_qs().filter(status=Project.Status.OPEN, category=project.category).exclude(pk=project.pk)[:3]
        return ctx


class SubmitProposalView(SeekerRequiredMixin, View):
    def post(self, request, slug):
        project = get_object_or_404(Project, slug=slug)
        form = ProposalForm(request.POST)
        if not form.is_valid():
            messages.error(request, _("تحقق من بيانات العرض."))
            return redirect(project.get_absolute_url())
        try:
            ProposalService().submit(project=project, freelancer=request.user, **form.cleaned_data)
            messages.success(request, _("تم إرسال عرضك بنجاح!"))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        return redirect(project.get_absolute_url())


class ProposalActionView(EmployerRequiredMixin, View):
    """Accept / shortlist / reject a proposal on one of my projects."""

    def post(self, request, pk, action):
        proposal = get_object_or_404(Proposal.objects.select_related("project"), pk=pk, project__owner=request.user)
        service = ProposalService()
        try:
            if action == "accept":
                service.accept(proposal, request.user)
                messages.success(request, _("تم قبول العرض وإسناد المشروع."))
            elif action in ("shortlisted", "rejected"):
                service.set_status(proposal, action, request.user)
                messages.success(request, _("تم تحديث حالة العرض."))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        return redirect("dashboard:employer_project_proposals", pk=proposal.project_id)


class WithdrawProposalView(SeekerRequiredMixin, View):
    def post(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk, freelancer=request.user)
        try:
            ProposalService().withdraw(proposal, request.user)
            messages.info(request, _("تم سحب العرض."))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        return redirect("dashboard:seeker_proposals")


class ProjectStatusView(EmployerRequiredMixin, View):
    def post(self, request, pk, action):
        project = get_object_or_404(Project, pk=pk, owner=request.user)
        try:
            if action == "complete":
                ProjectService.complete(project, request.user)
                messages.success(request, _("تم إنهاء المشروع. يمكنك الآن تقييم المستقل."))
                return redirect(project.get_absolute_url())
            if action == "cancel":
                ProjectService.cancel(project, request.user)
                messages.info(request, _("تم إلغاء المشروع."))
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
        return redirect("dashboard:employer_projects")
