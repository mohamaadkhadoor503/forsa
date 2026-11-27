from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Category, Job, Skill


class SkillsField(forms.CharField):
    """Comma separated skills, rendered as a tag input; creates missing skills."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("label", _("المهارات"))
        kwargs.setdefault("help_text", _("افصل بين المهارات بفاصلة"))
        kwargs.setdefault("widget", forms.TextInput(attrs={"data-tags": "1", "list": "skills-datalist"}))
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if hasattr(value, "__iter__") and not isinstance(value, str):
            names = []
            for item in value:
                if isinstance(item, Skill):
                    names.append(item.name)
                elif isinstance(item, int):
                    skill = Skill.objects.filter(pk=item).first()
                    if skill:
                        names.append(skill.name)
                else:
                    names.append(str(item))
            return ", ".join(names)
        return value

    def clean(self, value):
        value = super().clean(value)
        names = []
        for raw in (value or "").replace("،", ",").split(","):
            name = raw.strip()[:60]
            if name and name.lower() not in {n.lower() for n in names}:
                names.append(name)
        skills = []
        for name in names[:15]:
            skill = Skill.objects.filter(name__iexact=name).first() or Skill.objects.create(name=name)
            skills.append(skill)
        return skills


class JobForm(forms.ModelForm):
    skills = SkillsField()

    class Meta:
        model = Job
        fields = [
            "title", "category", "job_type", "workplace", "experience_level", "location",
            "salary_min", "salary_max", "currency", "deadline", "description",
            "responsibilities", "requirements", "benefits", "skills", "status",
        ]
        widgets = {
            "deadline": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 5}),
            "responsibilities": forms.Textarea(attrs={"rows": 4}),
            "requirements": forms.Textarea(attrs={"rows": 4}),
            "benefits": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        self.fields["status"].choices = [
            (Job.Status.PUBLISHED, _("نشر الآن")),
            (Job.Status.DRAFT, _("حفظ كمسودة")),
            (Job.Status.CLOSED, _("مغلقة")),
        ]

    def clean(self):
        data = super().clean()
        lo, hi = data.get("salary_min"), data.get("salary_max")
        if lo and hi and lo > hi:
            self.add_error("salary_max", _("يجب أن يكون الحد الأعلى أكبر من الأدنى."))
        return data
