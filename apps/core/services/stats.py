"""Platform statistics computed from real database data only."""
from dataclasses import asdict, dataclass

from django.contrib.auth import get_user_model
from django.core.cache import cache

CACHE_KEY = "platform-stats"
CACHE_SECONDS = 300


@dataclass(frozen=True)
class PlatformStats:
    users: int
    seekers: int
    employers: int
    open_jobs: int
    completed_projects: int
    successful_hires: int

    def as_dict(self):
        return asdict(self)


class PlatformStatsService:
    """Aggregates counts. Cached briefly to keep the homepage fast."""

    def get(self, use_cache: bool = True) -> PlatformStats:
        if use_cache:
            cached = cache.get(CACHE_KEY)
            if cached:
                return cached
        stats = self._compute()
        cache.set(CACHE_KEY, stats, CACHE_SECONDS)
        return stats

    @staticmethod
    def _compute() -> PlatformStats:
        from apps.applications.models import Application
        from apps.jobs.models import Job
        from apps.projects.models import Project, Proposal

        User = get_user_model()
        active = User.objects.filter(is_active=True)
        return PlatformStats(
            users=active.count(),
            seekers=active.filter(role=User.Role.SEEKER).count(),
            employers=active.filter(role=User.Role.EMPLOYER).count(),
            open_jobs=Job.objects.published().count(),
            completed_projects=Project.objects.filter(status=Project.Status.COMPLETED).count(),
            successful_hires=(
                Application.objects.filter(status=Application.Status.HIRED).count()
                + Proposal.objects.filter(status=Proposal.Status.ACCEPTED).count()
            ),
        )


def invalidate_stats():
    cache.delete(CACHE_KEY)
