from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView

from apps.core.forms import ContactForm
from apps.core.models import FAQ
from apps.core.services.stats import PlatformStatsService


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        from apps.companies.models import Company
        from apps.jobs.models import Category, Job
        from apps.jobs.services.saved_jobs import SavedJobService
        from apps.projects.views import projects_qs
        from apps.reviews.models import Testimonial
        from apps.talents.views import public_profiles

        ctx = super().get_context_data(**kwargs)
        published = Q(jobs__status=Job.Status.PUBLISHED)
        ctx["categories"] = Category.objects.filter(is_active=True).annotate(
            open_jobs=Count("jobs", filter=published, distinct=True),
            open_projects=Count("projects", filter=Q(projects__status="open"), distinct=True),
        )
        ctx["latest_jobs"] = Job.objects.published().with_relations().order_by("-is_featured", "-created_at")[:6]
        ctx["projects"] = projects_qs().filter(status="open")[:6]
        ctx["talents"] = public_profiles().order_by("-avg_rating", "-years_experience")[:10]
        # Only companies flagged by an admin as real partners are shown as "trusted".
        ctx["partners"] = Company.objects.filter(is_featured=True)[:16]
        ctx["testimonials"] = Testimonial.objects.filter(is_approved=True).select_related("author")[:10]
        ctx["stats"] = PlatformStatsService().get()
        ctx["saved_ids"] = SavedJobService.saved_ids(self.request.user)
        return ctx


class AboutView(TemplateView):
    template_name = "core/about.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["stats"] = PlatformStatsService().get()
        return ctx


class FAQView(TemplateView):
    template_name = "core/faq.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["faqs"] = FAQ.objects.filter(is_active=True)
        return ctx


class ContactView(FormView):
    template_name = "core/contact.html"
    form_class = ContactForm

    def get_initial(self):
        user = self.request.user
        if user.is_authenticated:
            return {"name": user.get_full_name(), "email": user.email}
        return {}

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("تم استلام رسالتك! سنعود إليك قريباً."))
        return redirect("core:contact")


class PrivacyView(TemplateView):
    template_name = "core/privacy.html"


class TermsView(TemplateView):
    template_name = "core/terms.html"
