from django import forms

from apps.jobs.forms import SkillsField

from .models import Education, Experience, PortfolioItem, SeekerProfile


class SeekerProfileForm(forms.ModelForm):
    skills = SkillsField()

    class Meta:
        model = SeekerProfile
        fields = ["headline", "specialization", "experience_level", "years_experience", "location",
                  "availability", "hourly_rate", "bio", "skills", "website", "github", "linkedin", "is_public"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 5})}


class CVForm(forms.ModelForm):
    class Meta:
        model = SeekerProfile
        fields = ["cv"]


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ["title", "company", "start_date", "end_date", "is_current", "description"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ["degree", "institution", "start_year", "end_year"]


class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = ["title", "description", "image", "url"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}
