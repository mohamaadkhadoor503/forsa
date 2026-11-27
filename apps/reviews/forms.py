from django import forms

from .models import Report, Review, Testimonial


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {"rating": forms.RadioSelect(choices=[(i, i) for i in range(5, 0, -1)]),
                   "comment": forms.Textarea(attrs={"rows": 3})}


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["role_title", "rating", "content"]
        widgets = {"rating": forms.RadioSelect(choices=[(i, i) for i in range(5, 0, -1)]),
                   "content": forms.Textarea(attrs={"rows": 4})}


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["reason", "details"]
        widgets = {"details": forms.Textarea(attrs={"rows": 3})}
