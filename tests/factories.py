from apps.accounts.models import User
from apps.accounts.services.registration import RegistrationService
from apps.jobs.models import Category, Job
from apps.projects.models import Project

PASSWORD = "S3cure!pass-123"


def make_seeker(n=1):
    return RegistrationService().register(email=f"seeker{n}@test.local", password=PASSWORD,
                                          first_name="باحث", last_name=str(n), role=User.Role.SEEKER)


def make_employer(n=1):
    return RegistrationService().register(email=f"emp{n}@test.local", password=PASSWORD, first_name="صاحب",
                                          last_name=str(n), role=User.Role.EMPLOYER, company_name=f"Company {n}")


def make_staff():
    return User.objects.create_superuser(email="admin@test.local", password=PASSWORD, username="admin")


def make_job(employer, **kw):
    defaults = dict(company=employer.company, posted_by=employer, title="مطور بايثون",
                    category=Category.objects.first(), description="desc", location="الرياض",
                    salary_min=1000, salary_max=2000)
    defaults.update(kw)
    return Job.objects.create(**defaults)


def make_project(employer, **kw):
    defaults = dict(owner=employer, title="مشروع تصميم", category=Category.objects.first(), description="desc",
                    budget_min=100, budget_max=300, duration_days=7)
    defaults.update(kw)
    return Project.objects.create(**defaults)
