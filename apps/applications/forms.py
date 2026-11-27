from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Application


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["cover_letter", "expected_salary", "cv"]
        widgets = {"cover_letter": forms.Textarea(attrs={"rows": 6, "placeholder": _("عرّف بنفسك ولماذا أنت مناسب لهذه الوظيفة...")})}
        help_texts = {"cv": _("اتركه فارغاً لاستخدام السيرة الذاتية المرفوعة في ملفك")}


class StatusChangeForm(forms.Form):
    status = forms.ChoiceField(choices=Application.Status.choices)
    note = forms.CharField(max_length=255, required=False)
