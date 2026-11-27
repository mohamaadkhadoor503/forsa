from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ["core:home", "jobs:list", "projects:list", "talents:list", "companies:list",
                "core:about", "core:contact", "core:faq", "core:privacy", "core:terms"]

    def location(self, item):
        return reverse(item)


class JobSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        from apps.jobs.models import Job
        return Job.objects.published()

    def lastmod(self, obj):
        return obj.updated_at


class ProjectSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7

    def items(self):
        from apps.projects.models import Project
        return Project.objects.filter(status="open")

    def lastmod(self, obj):
        return obj.updated_at


class CompanySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        from apps.companies.models import Company
        return Company.objects.all()


sitemaps = {"static": StaticSitemap, "jobs": JobSitemap, "projects": ProjectSitemap, "companies": CompanySitemap}
