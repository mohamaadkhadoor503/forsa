from django import forms

from .models import ContactMessage, FAQ, SiteSettings


class ContactForm(forms.ModelForm):
    # Simple honeypot against bots
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 5})}

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("bot")
        return ""


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = "__all__"
        widgets = {"about": forms.Textarea(attrs={"rows": 3})}


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = "__all__"
