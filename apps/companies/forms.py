from django import forms

from .models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "tagline", "logo", "cover", "industry", "size", "location",
                  "founded_year", "website", "linkedin", "description"]
        widgets = {"description": forms.Textarea(attrs={"rows": 6})}
