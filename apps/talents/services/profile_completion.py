"""Profile completeness scoring.

Each rule is an independent check; the calculator just sums weights. Adding
a rule never changes existing ones.
"""
from dataclasses import dataclass
from typing import Callable

from django.utils.translation import gettext_lazy as _


@dataclass(frozen=True)
class CompletionRule:
    label: str
    weight: int
    check: Callable


DEFAULT_RULES = [
    CompletionRule(_("الصورة الشخصية"), 10, lambda p: bool(p.user.avatar)),
    CompletionRule(_("المسمى المهني"), 10, lambda p: bool(p.headline)),
    CompletionRule(_("النبذة"), 15, lambda p: len(p.bio or "") >= 40),
    CompletionRule(_("التخصص"), 10, lambda p: p.specialization_id is not None),
    CompletionRule(_("المهارات (3 على الأقل)"), 15, lambda p: p.skills.count() >= 3),
    CompletionRule(_("السيرة الذاتية"), 15, lambda p: bool(p.cv)),
    CompletionRule(_("الخبرات"), 10, lambda p: p.experiences.exists()),
    CompletionRule(_("معرض الأعمال"), 10, lambda p: p.portfolio.exists()),
    CompletionRule(_("الموقع"), 5, lambda p: bool(p.location)),
]


class ProfileCompletionCalculator:
    def __init__(self, rules=None):
        self.rules = rules or DEFAULT_RULES

    def evaluate(self, profile):
        total = sum(r.weight for r in self.rules)
        done, missing = 0, []
        for rule in self.rules:
            if rule.check(profile):
                done += rule.weight
            else:
                missing.append(rule.label)
        return {"percent": round(done * 100 / total) if total else 100, "missing": missing}
