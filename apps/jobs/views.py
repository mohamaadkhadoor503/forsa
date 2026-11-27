from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import DetailView, ListView

from apps.core.mixins import PartialTemplateMixin, QueryStringMixin

from .filters import JobFilterSet
from .models import Category, ExperienceLevel, Job, Skill, Workplace
from .services.saved_jobs import SavedJobService


class JobListView(PartialTemplateMixin, QueryStringMixin, ListView):
    template_name = "jobs/list.html"
    partial_template_name = "jobs/_results.html"
    context_object_name = "jobs"
    paginate_by = 12

    def get_queryset(self):
        self.filterset = JobFilterSet(self.request.GET, Job.objects.published().with_relations())
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            filterset=self.filterset,
            categories=Category.objects.filter(is_active=True),
            workplaces=Workplace.choices,
            job_types=Job.JobType.choices,
            levels=ExperienceLevel.choices,
            popular_skills=Skill.objects.all()[:40],
            saved_ids=SavedJobService.saved_ids(self.request.user),
            view_mode=self.request.GET.get("view", "grid"),
        )
        return ctx


class JobDetailView(DetailView):
    template_name = "jobs/detail.html"
    context_object_name = "job"

    def get_queryset(self):
        qs = Job.objects.with_relations()
        user = self.request.user
        if user.is_authenticated and user.is_employer:
            from django.db.models import Q
            return qs.filter(Q(status=Job.Status.PUBLISHED) | Q(company__owner=user))
        if user.is_authenticated and user.is_staff:
            return qs
        return qs.filter(status__in=[Job.Status.PUBLISHED, Job.Status.CLOSED])

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        Job.objects.filter(pk=obj.pk).update(views_count=F("views_count") + 1)
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        job = self.object
        user = self.request.user
        ctx["similar_jobs"] = (
            Job.objects.published().with_relations().filter(category=job.category).exclude(pk=job.pk)[:3]
        )
        ctx["is_saved"] = job.pk in SavedJobService.saved_ids(user)
        ctx["application"] = None
        if user.is_authenticated and user.is_seeker:
            ctx["application"] = job.applications.filter(applicant=user).first()
        return ctx


class ToggleSaveJobView(LoginRequiredMixin, View):
    def post(self, request, slug):
        job = get_object_or_404(Job, slug=slug)
        saved = SavedJobService.toggle(request.user, job)
        msg = _("تم حفظ الوظيفة") if saved else _("تمت إزالة الوظيفة من المحفوظات")
        if request.headers.get("X-Requested-With") == "fetch":
            return JsonResponse({"saved": saved, "message": msg})
        messages.success(request, msg)
        return redirect(request.POST.get("next") or job.get_absolute_url())
