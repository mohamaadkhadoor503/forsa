from django.urls import path
from django.views.generic import TemplateView

from .views import pages

app_name = "core"

urlpatterns = [
    path("", pages.HomeView.as_view(), name="home"),
    path("about/", pages.AboutView.as_view(), name="about"),
    path("contact/", pages.ContactView.as_view(), name="contact"),
    path("faq/", pages.FAQView.as_view(), name="faq"),
    path("privacy/", pages.PrivacyView.as_view(), name="privacy"),
    path("terms/", pages.TermsView.as_view(), name="terms"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain"), name="robots"),
]
