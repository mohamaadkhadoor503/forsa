"""Tiny composable filtering layer.

A ``FilterSet`` is configured with independent filter objects; each object
knows how to read one query parameter and narrow a queryset. New filters can
be added without touching existing ones (Open/Closed), and every listing page
(jobs, projects, talents, companies) reuses the same machinery.
"""
from dataclasses import dataclass
from dataclasses import field as dc_field
from decimal import Decimal, InvalidOperation

from django.db.models import Q


@dataclass
class ActiveFilter:
    param: str
    value: str
    label: str


@dataclass
class BaseFilter:
    param: str
    label: str = ""

    def get_value(self, data):
        value = data.get(self.param, "")
        return value.strip() if isinstance(value, str) else value

    def apply(self, qs, value):  # pragma: no cover - interface
        raise NotImplementedError

    def display(self, value):
        return value


@dataclass
class KeywordFilter(BaseFilter):
    fields: tuple = ()

    def apply(self, qs, value):
        query = Q()
        for term in value.split()[:6]:
            term_q = Q()
            for f in self.fields:
                term_q |= Q(**{f"{f}__icontains": term})
            query &= term_q
        return qs.filter(query)


@dataclass
class ExactFilter(BaseFilter):
    field: str = ""
    choices: dict = dc_field(default_factory=dict)

    def apply(self, qs, value):
        if self.choices and value not in self.choices:
            return qs
        return qs.filter(**{self.field: value})

    def display(self, value):
        return self.choices.get(value, value)


@dataclass
class ContainsFilter(BaseFilter):
    field: str = ""

    def apply(self, qs, value):
        return qs.filter(**{f"{self.field}__icontains": value})


@dataclass
class NumberFilter(BaseFilter):
    field: str = ""
    lookup: str = "gte"

    def apply(self, qs, value):
        try:
            number = Decimal(value)
        except (InvalidOperation, TypeError):
            return qs
        return qs.filter(**{f"{self.field}__{self.lookup}": number})


@dataclass
class SkillsFilter(BaseFilter):
    field: str = "skills__slug"

    def get_value(self, data):
        values = data.getlist(self.param) if hasattr(data, "getlist") else data.get(self.param, [])
        return [v for v in values if v]

    def apply(self, qs, value):
        return qs.filter(**{f"{self.field}__in": value}).distinct()

    def display(self, value):
        return value


@dataclass
class BooleanFilter(BaseFilter):
    field: str = ""
    expected: object = True

    def apply(self, qs, value):
        if value in ("1", "true", "on"):
            return qs.filter(**{self.field: self.expected})
        return qs


class FilterSet:
    filters: list = []
    orderings: dict = {}
    default_ordering: str = ""

    def __init__(self, data, queryset):
        self.data = data
        self.queryset = queryset
        self._active = []

    @property
    def qs(self):
        qs = self.queryset
        self._active = []
        for flt in self.filters:
            value = flt.get_value(self.data)
            if not value:
                continue
            qs = flt.apply(qs, value)
            values = value if isinstance(value, list) else [value]
            for v in values:
                self._active.append(ActiveFilter(flt.param, v, f"{flt.label}: {flt.display(v)}" if flt.label else str(flt.display(v))))
        order = self.data.get("sort") or self.default_ordering
        ordering = self.orderings.get(order) or self.orderings.get(self.default_ordering)
        if ordering:
            qs = qs.order_by(*ordering[0])
        return qs

    @property
    def active(self):
        return self._active

    @classmethod
    def sort_options(cls):
        return [(key, label) for key, (_fields, label) in cls.orderings.items()]
