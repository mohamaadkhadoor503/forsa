"""Job recommendations for a seeker.

The scoring strategy is injected so it can be replaced (e.g. by an ML
model) without changing callers (Dependency Inversion).
"""
from typing import Protocol

from django.db.models import Count, Q

from apps.jobs.models import Job


class RecommendationStrategy(Protocol):
    def recommend(self, profile, limit: int): ...


class SkillOverlapStrategy:
    def recommend(self, profile, limit):
        qs = Job.objects.published().with_relations()
        skill_ids = list(profile.skills.values_list("id", flat=True))
        if not skill_ids and not profile.specialization_id:
            return list(qs[:limit])
        q = Q(skills__in=skill_ids)
        if profile.specialization_id:
            q |= Q(category_id=profile.specialization_id)
        return list(
            qs.filter(q)
            .annotate(score=Count("skills", filter=Q(skills__in=skill_ids), distinct=True))
            .order_by("-score", "-created_at")
            .distinct()[:limit]
        )


class RecommendationService:
    def __init__(self, strategy: RecommendationStrategy | None = None):
        self.strategy = strategy or SkillOverlapStrategy()

    def for_profile(self, profile, limit=6):
        return self.strategy.recommend(profile, limit)
