"""Smoke + permission tests: every page renders for the right roles, and is protected for the wrong ones."""
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.applications.models import Application
from apps.jobs.models import Job
from apps.messaging.models import Conversation
from apps.projects.models import Project

PUBLIC = ["core:home", "core:about", "core:contact", "core:faq", "core:privacy", "core:terms",
          "jobs:list", "projects:list", "talents:list", "companies:list",
          "accounts:login", "accounts:choose_type", "accounts:password_reset", "sitemap", "core:robots"]
SEEKER = ["dashboard:seeker_home", "dashboard:seeker_profile", "dashboard:seeker_cv", "dashboard:seeker_portfolio",
          "dashboard:seeker_experience", "dashboard:seeker_recommended", "dashboard:seeker_applications",
          "dashboard:seeker_proposals", "dashboard:seeker_saved"]
EMPLOYER = ["dashboard:employer_home", "dashboard:employer_company", "dashboard:employer_jobs",
            "dashboard:employer_job_create", "dashboard:employer_applications", "dashboard:employer_projects",
            "dashboard:employer_project_create", "dashboard:employer_favorites"]
STAFF = ["dashboard:admin_home", "dashboard:admin_users", "dashboard:admin_companies", "dashboard:admin_jobs",
         "dashboard:admin_projects", "dashboard:admin_categories", "dashboard:admin_category_create",
         "dashboard:admin_reports", "dashboard:admin_content", "dashboard:admin_settings"]
COMMON = ["dashboard:settings", "messaging:inbox", "notifications:list", "reviews:testimonial"]


@override_settings(STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                             "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class PageSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0)
        cls.seeker = User.objects.get(email="seeker1@demo.local")
        cls.employer = User.objects.get(email="employer1@demo.local")
        cls.staff = User.objects.get(email="admin@demo.local")

    def assertPages(self, names, status=200):
        for name in names:
            with self.subTest(page=name):
                resp = self.client.get(reverse(name))
                self.assertEqual(resp.status_code, status, f"{name} -> {resp.status_code}")

    def test_public_pages(self):
        self.assertPages(PUBLIC)

    def test_public_pages_english(self):
        self.client.cookies["django_language"] = "en"
        resp = self.client.get(reverse("core:home"))
        self.assertContains(resp, 'dir="ltr"')
        self.assertContains(resp, "Find a job")

    def test_detail_pages(self):
        job = Job.objects.first()
        project = Project.objects.filter(status="open").first()
        urls = [job.get_absolute_url(), project.get_absolute_url(), job.company.get_absolute_url(),
                self.seeker.profile.get_absolute_url(), reverse("accounts:signup", args=["seeker"]),
                reverse("accounts:signup", args=["employer"])]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_partial_results(self):
        resp = self.client.get(reverse("jobs:list") + "?workplace=remote&sort=salary", HTTP_X_PARTIAL="1")
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "<html")

    def test_seeker_pages(self):
        self.client.force_login(self.seeker)
        self.assertPages(SEEKER + COMMON)
        job = Job.objects.published().exclude(applications__applicant=self.seeker).first()
        self.assertEqual(self.client.get(reverse("applications:apply", args=[job.slug])).status_code, 200)
        self.assertPages(EMPLOYER[:1] + STAFF[:1], status=403)

    def test_employer_pages(self):
        self.client.force_login(self.employer)
        self.assertPages(EMPLOYER + COMMON)
        job = self.employer.company.jobs.first()
        project = self.employer.projects.first()
        for url in [reverse("dashboard:employer_job_edit", args=[job.pk]),
                    reverse("dashboard:employer_job_applications", args=[job.pk]),
                    reverse("dashboard:employer_project_proposals", args=[project.pk])]:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertPages(SEEKER[:1] + STAFF[:1], status=403)

    def test_staff_pages(self):
        self.client.force_login(self.staff)
        self.assertPages(STAFF + COMMON)

    def test_anonymous_redirected_from_dashboard(self):
        resp = self.client.get(reverse("dashboard:seeker_home"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp["Location"])

    def test_employer_cannot_edit_foreign_job(self):
        other = User.objects.get(email="employer2@demo.local")
        job = other.company.jobs.first()
        self.client.force_login(self.employer)
        self.assertEqual(self.client.get(reverse("dashboard:employer_job_edit", args=[job.pk])).status_code, 404)

    def test_404_page(self):
        resp = self.client.get("/jobs/does-not-exist-xyz/")
        self.assertEqual(resp.status_code, 404)


class FlowTests(TestCase):
    def test_signup_login_apply_flow(self):
        call_command("seed_demo", verbosity=0)
        resp = self.client.post(reverse("accounts:signup", args=["seeker"]), {
            "first_name": "علي", "last_name": "حسن", "email": "ali@example.com",
            "password1": "Very$trong-pass9", "password2": "Very$trong-pass9", "terms": "on"})
        self.assertRedirects(resp, reverse("dashboard:home"), target_status_code=302)
        job = Job.objects.published().first()
        resp = self.client.post(reverse("applications:apply", args=[job.slug]), {"cover_letter": "مهتم جداً"})
        self.assertRedirects(resp, reverse("dashboard:seeker_applications"))
        self.assertTrue(Application.objects.filter(applicant__email="ali@example.com", job=job).exists())

        # save job via fetch
        resp = self.client.post(reverse("jobs:toggle_save", args=[job.slug]), HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(resp.json()["saved"], True)

        # start a conversation with the employer and send a message
        resp = self.client.post(reverse("messaging:start", args=[job.company.owner.pk]), {"body": "مرحباً"})
        conv = Conversation.objects.get(participants__email="ali@example.com")
        self.assertRedirects(resp, reverse("messaging:detail", args=[conv.pk]))
        poll = self.client.get(reverse("messaging:poll", args=[conv.pk]) + "?after=0").json()
        self.assertEqual(len(poll["messages"]), 1)

        self.client.post(reverse("accounts:logout"))
        resp = self.client.post(reverse("accounts:login"), {"email": "ALI@example.com", "password": "Very$trong-pass9"})
        self.assertRedirects(resp, reverse("dashboard:home"), target_status_code=302)

    def test_employer_posts_job(self):
        from apps.jobs.models import Category
        self.client.post(reverse("accounts:signup", args=["employer"]), {
            "first_name": "منى", "last_name": "س", "email": "mona@example.com", "company_name": "شركة منى",
            "password1": "Very$trong-pass9", "password2": "Very$trong-pass9", "terms": "on"})
        resp = self.client.post(reverse("dashboard:employer_job_create"), {
            "title": "مصمم", "category": Category.objects.first().pk, "job_type": "full_time", "workplace": "remote",
            "experience_level": "mid", "location": "عن بعد", "currency": "$", "description": "وصف",
            "skills": "Figma, UI/UX، Photoshop", "status": "published"})
        self.assertRedirects(resp, reverse("dashboard:employer_jobs"))
        job = Job.objects.get(title="مصمم")
        self.assertEqual(job.skills.count(), 3)
