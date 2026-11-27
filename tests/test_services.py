from django.core.exceptions import PermissionDenied, ValidationError
from django.http import QueryDict
from django.test import TestCase

from apps.applications.models import Application
from apps.applications.services.applications import ApplicationService
from apps.core.services.stats import PlatformStatsService
from apps.jobs.filters import JobFilterSet
from apps.jobs.models import Job, Skill
from apps.jobs.services.saved_jobs import SavedJobService
from apps.notifications.models import Notification
from apps.notifications.services.notifier import NotificationService
from apps.projects.models import Project, Proposal
from apps.projects.services.proposals import ProjectService, ProposalService
from apps.reviews.services import ReviewService
from apps.talents.services.profile_completion import ProfileCompletionCalculator

from .factories import make_employer, make_job, make_project, make_seeker


class InMemoryChannel:
    """Test double proving the notifier depends on an abstraction."""

    def __init__(self):
        self.sent = []

    def send(self, recipient, title, body, url, kind):
        self.sent.append((recipient, title))


class RegistrationTests(TestCase):
    def test_roles_get_their_profiles(self):
        self.assertTrue(hasattr(make_seeker(), "profile"))
        self.assertTrue(hasattr(make_employer(), "company"))

    def test_categories_seeded(self):
        from apps.jobs.models import Category
        self.assertEqual(Category.objects.count(), 10)


class ApplicationServiceTests(TestCase):
    def setUp(self):
        self.emp, self.seeker = make_employer(), make_seeker()
        self.job = make_job(self.emp)
        self.channel = InMemoryChannel()
        self.service = ApplicationService(NotificationService([self.channel]))

    def test_apply_notifies_employer_and_logs_event(self):
        app = self.service.apply(job=self.job, applicant=self.seeker, cover_letter="hi")
        self.assertEqual(app.events.count(), 1)
        self.assertEqual(self.channel.sent[0][0], self.emp)

    def test_cannot_apply_twice(self):
        self.service.apply(job=self.job, applicant=self.seeker, cover_letter="hi")
        with self.assertRaises(ValidationError):
            self.service.apply(job=self.job, applicant=self.seeker, cover_letter="again")

    def test_employer_cannot_apply(self):
        with self.assertRaises(PermissionDenied):
            self.service.apply(job=self.job, applicant=self.emp, cover_letter="x")

    def test_closed_job_rejects(self):
        self.job.status = Job.Status.CLOSED
        self.job.save()
        with self.assertRaises(ValidationError):
            self.service.apply(job=self.job, applicant=self.seeker, cover_letter="x")

    def test_status_transitions(self):
        app = self.service.apply(job=self.job, applicant=self.seeker, cover_letter="hi")
        self.service.change_status(app, "interview", self.emp)
        self.assertEqual(app.status, "interview")
        with self.assertRaises(ValidationError):
            self.service.change_status(app, "submitted", self.emp)
        other = make_employer(2)
        with self.assertRaises(PermissionDenied):
            self.service.change_status(app, "offered", other)

    def test_hire_counts_in_stats(self):
        app = self.service.apply(job=self.job, applicant=self.seeker, cover_letter="hi")
        for st in ("shortlisted", "offered", "hired"):
            self.service.change_status(app, st, self.emp)
        self.assertEqual(PlatformStatsService().get(use_cache=False).successful_hires, 1)

    def test_withdraw(self):
        app = self.service.apply(job=self.job, applicant=self.seeker, cover_letter="hi")
        self.service.withdraw(app, self.seeker)
        self.assertEqual(app.status, Application.Status.WITHDRAWN)


class ProposalServiceTests(TestCase):
    def setUp(self):
        self.emp = make_employer()
        self.s1, self.s2 = make_seeker(1), make_seeker(2)
        self.project = make_project(self.emp)
        self.service = ProposalService(NotificationService([InMemoryChannel()]))

    def test_accept_rejects_others_and_assigns(self):
        p1 = self.service.submit(project=self.project, freelancer=self.s1, cover_letter="a", bid_amount=200, delivery_days=5)
        p2 = self.service.submit(project=self.project, freelancer=self.s2, cover_letter="b", bid_amount=250, delivery_days=5)
        self.service.accept(p1, self.emp)
        p2.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(p2.status, Proposal.Status.REJECTED)
        self.assertEqual(self.project.status, Project.Status.IN_PROGRESS)
        self.assertEqual(self.project.freelancer, self.s1)

    def test_review_only_after_completion(self):
        p1 = self.service.submit(project=self.project, freelancer=self.s1, cover_letter="a", bid_amount=200, delivery_days=5)
        self.service.accept(p1, self.emp)
        with self.assertRaises(ValidationError):
            ReviewService.create(project=self.project, reviewer=self.emp, rating=5)
        ProjectService.complete(self.project, self.emp)
        ReviewService.create(project=self.project, reviewer=self.emp, rating=5)
        self.assertEqual(self.s1.reviews_received.count(), 1)


class FilterAndHelpersTests(TestCase):
    def setUp(self):
        self.emp = make_employer()
        py = Skill.objects.get_or_create(name="Python")[0]
        self.remote = make_job(self.emp, title="Remote Python", workplace="remote", salary_min=3000, salary_max=4000)
        self.remote.skills.add(py)
        self.onsite = make_job(self.emp, title="Onsite Designer", workplace="onsite", salary_min=500, salary_max=800)

    def _filter(self, qs):
        fs = JobFilterSet(QueryDict(qs), Job.objects.published())
        return list(fs.qs), fs

    def test_workplace_and_salary_filters(self):
        res, fs = self._filter("workplace=remote")
        self.assertEqual(res, [self.remote])
        self.assertEqual(len(fs.active), 1)
        res, _ = self._filter("salary_min=2000")
        self.assertEqual(res, [self.remote])

    def test_skill_and_keyword_filters(self):
        res, _ = self._filter("skill=python")
        self.assertEqual(res, [self.remote])
        res, _ = self._filter("q=Designer")
        self.assertEqual(res, [self.onsite])

    def test_invalid_choice_is_ignored(self):
        res, _ = self._filter("workplace=moon")
        self.assertEqual(len(res), 2)

    def test_save_toggle(self):
        s = make_seeker()
        self.assertTrue(SavedJobService.toggle(s, self.remote))
        self.assertFalse(SavedJobService.toggle(s, self.remote))

    def test_profile_completion(self):
        s = make_seeker()
        result = ProfileCompletionCalculator().evaluate(s.profile)
        self.assertLess(result["percent"], 20)
        self.assertTrue(result["missing"])

    def test_db_notification_channel(self):
        s = make_seeker()
        NotificationService().notify(s, "title", "body")
        self.assertEqual(Notification.objects.filter(recipient=s).count(), 1)
