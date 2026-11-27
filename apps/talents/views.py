from django.contrib import messages
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _l
from django.views import View
from django.views.generic import DetailView, ListView

from apps.companies.models import FavoriteTalent
from apps.core.filtering import (
    ContainsFilter, ExactFilter, FilterSet, KeywordFilter, NumberFilter, SkillsFilter,
)
from apps.core.mixins import EmployerRequiredMixin, PartialTemplateMixin, QueryStringMixin
from apps.jobs.models import Category, ExperienceLevel, Skill

from .models import SeekerProfile


class TalentFilterSet(FilterSet):
    filters = [
        KeywordFilter("q", _l("كلمة"), fields=("headline", "bio", "user__first_name", "user__last_name", "skills__name")),
        ExactFilter("category", _l("التخصص"), field="specialization__slug"),
        ContainsFilter("location", _l("الموقع"), field="location"),
        ExactFilter("level", "", field="experience_level", choices=dict(ExperienceLevel.choices)),
        ExactFilter("availability", "", field="availability", choices=dict(SeekerProfile.Availability.choices)),
        NumberFilter("min_years", _l("خبرة من"), field="years_experience", lookup="gte"),
        NumberFilter("max_rate", _l("سعر حتى"), field="hourly_rate", lookup="lte"),
        SkillsFilter("skill", _l("مهارة")),
    ]
    orderings = {
        "rating": (("-avg_rating", "-years_experience"), _l("الأعلى تقييماً")),
        "experience": (("-years_experience",), _l("الأكثر خبرة")),
        "newest": (("-created_at",), _l("الأحدث")),
    }
    default_ordering = "rating"

    @property
    def qs(self):
        return super().qs.distinct()


def public_profiles():
    return (
        SeekerProfile.objects.filter(is_public=True, user__is_active=True)
        .select_related("user", "specialization")
        .prefetch_related("skills", "portfolio")
        .annotate(avg_rating=Avg("user__reviews_received__rating"),
                  reviews_count=Count("user__reviews_received", distinct=True))
    )


class TalentListView(PartialTemplateMixin, QueryStringMixin, ListView):
    template_name = "talents/list.html"
    partial_template_name = "talents/_results.html"
    context_object_name = "profiles"
    paginate_by = 12

    def get_queryset(self):
        self.filterset = TalentFilterSet(self.request.GET, public_profiles())
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            filterset=self.filterset,
            categories=Category.objects.filter(is_active=True),
            levels=ExperienceLevel.choices,
            availabilities=SeekerProfile.Availability.choices,
            popular_skills=Skill.objects.all()[:40],
            favorite_ids=self._favorite_ids(),
        )
        return ctx

    def _favorite_ids(self):
        user = self.request.user
        if user.is_authenticated and user.is_employer:
            return set(FavoriteTalent.objects.filter(employer=user).values_list("profile_id", flat=True))
        return set()


class TalentDetailView(DetailView):
    template_name = "talents/detail.html"
    context_object_name = "profile"

    def get_queryset(self):
        qs = public_profiles()
        user = self.request.user
        if user.is_authenticated:
            # owners can preview their own private profile
            qs = (SeekerProfile.objects.filter(is_public=True) | SeekerProfile.objects.filter(user=user))
            qs = qs.select_related("user", "specialization").prefetch_related("skills", "portfolio").annotate(
                avg_rating=Avg("user__reviews_received__rating"),
                reviews_count=Count("user__reviews_received", distinct=True))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["reviews"] = self.object.user.reviews_received.select_related("reviewer")[:10]
        ctx["is_favorite"] = (
            user.is_authenticated and user.is_employer
            and FavoriteTalent.objects.filter(employer=user, profile=self.object).exists()
        )
        return ctx


class ToggleFavoriteTalentView(EmployerRequiredMixin, View):
    def post(self, request, pk):
        profile = get_object_or_404(SeekerProfile, pk=pk)
        fav, created = FavoriteTalent.objects.get_or_create(employer=request.user, profile=profile)
        if not created:
            fav.delete()
            messages.info(request, _("تمت الإزالة من المرشحين المفضلين"))
        else:
            messages.success(request, _("تمت الإضافة إلى المرشحين المفضلين"))
        return redirect(request.POST.get("next") or profile.get_absolute_url())
