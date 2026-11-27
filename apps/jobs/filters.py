from django.utils.translation import gettext_lazy as _

from apps.core.filtering import (
    ContainsFilter, ExactFilter, FilterSet, KeywordFilter, NumberFilter, SkillsFilter,
)

from .models import ExperienceLevel, Job, Workplace


class JobFilterSet(FilterSet):
    filters = [
        KeywordFilter("q", _("كلمة"), fields=("title", "description", "company__name", "skills__name")),
        ContainsFilter("title", _("المسمى"), field="title"),
        ContainsFilter("location", _("الموقع"), field="location"),
        ExactFilter("category", _("التخصص"), field="category__slug"),
        ExactFilter("workplace", "", field="workplace", choices=dict(Workplace.choices)),
        ExactFilter("type", "", field="job_type", choices=dict(Job.JobType.choices)),
        ExactFilter("level", "", field="experience_level", choices=dict(ExperienceLevel.choices)),
        NumberFilter("salary_min", _("راتب من"), field="salary_max", lookup="gte"),
        NumberFilter("salary_max", _("راتب حتى"), field="salary_min", lookup="lte"),
        SkillsFilter("skill", _("مهارة")),
    ]
    orderings = {
        "newest": (("-is_featured", "-created_at"), _("الأحدث")),
        "salary": (("-salary_max", "-created_at"), _("الأعلى راتباً")),
        "relevant": (("-is_featured", "-views_count", "-created_at"), _("الأكثر ملاءمة")),
    }
    default_ordering = "newest"

    @property
    def qs(self):
        return super().qs.distinct()
