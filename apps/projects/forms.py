from django import forms
from django.utils.translation import gettext_lazy as _

from apps.jobs.forms import SkillsField
from apps.jobs.models import Category

from .models import Project, Proposal


class ProjectForm(forms.ModelForm):
    skills = SkillsField()

    class Meta:
        model = Project
        fields = ["title", "category", "experience_level", "budget_type", "budget_min", "budget_max",
                  "duration_days", "description", "deliverables", "skills"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "deliverables": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)

    def clean(self):
        data = super().clean()
        lo, hi = data.get("budget_min"), data.get("budget_max")
        if lo is not None and hi is not None and lo > hi:
            self.add_error("budget_max", _("يجب أن يكون الحد الأعلى أكبر من الأدنى."))
        return data


class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ["bid_amount", "delivery_days", "cover_letter"]
        widgets = {"cover_letter": forms.Textarea(attrs={"rows": 6, "placeholder": _("اشرح خطتك لتنفيذ المشروع وخبراتك المشابهة...")})}
