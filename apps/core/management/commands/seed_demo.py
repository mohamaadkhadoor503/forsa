"""Populate a LOCAL database with clearly-labelled demo data for manual testing.

    python manage.py seed_demo

Every demo company is suffixed with "(تجريبي)" and every demo account uses the
@demo.local domain so demo content can never be mistaken for real activity.
Remove it with:  python manage.py seed_demo --clear
"""
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.accounts.services.registration import RegistrationService
from apps.applications.models import Application, ApplicationEvent
from apps.companies.models import Company
from apps.core.services.stats import invalidate_stats
from apps.jobs.models import Category, Job, Skill
from apps.projects.models import Project, Proposal
from apps.reviews.models import Review, Testimonial
from apps.talents.models import Experience, PortfolioItem

PASSWORD = "Demo@12345"
DOMAIN = "demo.local"

EMPLOYERS = [
    ("سارة", "العتيبي", "نماء للتقنية (تجريبي)", "programming", "الرياض", "حلول برمجية للشركات الناشئة والمتوسطة"),
    ("خالد", "المصري", "أفق للتسويق الرقمي (تجريبي)", "digital-marketing", "القاهرة", "وكالة تسويق رقمي متكاملة"),
    ("ليلى", "حداد", "درع للأمن السيبراني (تجريبي)", "cybersecurity", "عمّان", "حماية البنية التحتية الرقمية"),
]

SEEKERS = [
    ("أحمد", "الخطيب", "مطوّر Full-Stack", "programming", 5, ["Python", "Django", "React", "PostgreSQL"], "دمشق"),
    ("مريم", "السالم", "مصممة UI/UX", "graphic-design", 4, ["Figma", "UI/UX", "Illustrator"], "دبي"),
    ("يوسف", "الحسن", "أخصائي تسويق رقمي", "digital-marketing", 3, ["SEO", "تسويق عبر وسائل التواصل", "كتابة المحتوى"], "الدار البيضاء"),
    ("نور", "القاسم", "مهندسة تعلم آلي", "ai", 6, ["Python", "Machine Learning", "تحليل البيانات"], "عن بعد"),
    ("عمر", "الزعبي", "محلل أمن معلومات", "cybersecurity", 4, ["اختبار الاختراق", "Docker", "AWS"], "عمّان"),
    ("رهف", "يوسف", "صانعة محتوى ومونتير", "content", 2, ["مونتاج الفيديو", "Premiere Pro", "After Effects"], "بيروت"),
]

JOBS = [
    ("مطوّر Back-end (Django)", "programming", "remote", "full_time", "mid", 2000, 3200, ["Python", "Django", "PostgreSQL"]),
    ("مطوّر واجهات أمامية React", "programming", "hybrid", "full_time", "mid", 1800, 2800, ["React", "JavaScript"]),
    ("مهندس DevOps", "programming", "onsite", "full_time", "senior", 3000, 4500, ["Docker", "AWS"]),
    ("مصمم منتجات UI/UX", "graphic-design", "remote", "contract", "mid", 1500, 2500, ["Figma", "UI/UX"]),
    ("مدير حملات إعلانية", "digital-marketing", "onsite", "full_time", "senior", 1700, 2600, ["تسويق عبر وسائل التواصل"]),
    ("أخصائي SEO", "digital-marketing", "remote", "part_time", "entry", 800, 1200, ["SEO", "كتابة المحتوى"]),
    ("محلل SOC", "cybersecurity", "hybrid", "full_time", "mid", 2200, 3400, ["اختبار الاختراق"]),
    ("متدرب أمن معلومات", "cybersecurity", "onsite", "internship", "entry", 400, 600, []),
    ("مهندس تعلم آلي", "ai", "remote", "full_time", "senior", 3500, 5000, ["Python", "Machine Learning"]),
    ("محاسب أول", "finance", "onsite", "full_time", "mid", 1400, 2000, ["المحاسبة", "Excel"]),
]

PROJECTS = [
    ("تصميم هوية بصرية لمتجر إلكتروني", "graphic-design", 300, 600, 14, ["Illustrator", "Photoshop"]),
    ("تطوير لوحة تحكم بـ Django", "programming", 800, 1500, 30, ["Django", "Python"]),
    ("إدارة حسابات التواصل لمدة شهر", "digital-marketing", 400, 700, 30, ["تسويق عبر وسائل التواصل"]),
    ("مونتاج 10 فيديوهات قصيرة", "content", 250, 450, 10, ["مونتاج الفيديو", "Premiere Pro"]),
    ("نموذج تصنيف نصوص عربية", "ai", 1200, 2500, 45, ["Machine Learning", "Python"]),
    ("فحص أمني لتطبيق ويب", "cybersecurity", 900, 1600, 15, ["اختبار الاختراق"]),
]

LOREM = ("نبحث عن شخص شغوف ومنظم للانضمام إلى فريقنا والمساهمة في بناء منتجات يستخدمها آلاف المستخدمين. "
         "ستعمل ضمن فريق متعاون وتحصل على فرص حقيقية للتعلم والنمو.")


class Command(BaseCommand):
    help = "Seed clearly-labelled demo data for local testing (never for production)."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete all demo data")

    @transaction.atomic
    def handle(self, *args, **opts):
        if opts["clear"]:
            n, _ = User.objects.filter(email__endswith=f"@{DOMAIN}").delete()
            invalidate_stats()
            self.stdout.write(self.style.WARNING(f"Deleted demo data ({n} rows)."))
            return
        if User.objects.filter(email=f"admin@{DOMAIN}").exists():
            self.stdout.write("Demo data already exists. Use --clear first to recreate it.")
            return

        random.seed(7)
        service = RegistrationService()
        User.objects.create_superuser(email=f"admin@{DOMAIN}", password=PASSWORD, username="admin-demo",
                                      first_name="مدير", last_name="المنصة")
        cats = {c.slug: c for c in Category.objects.all()}
        skill = lambda name: Skill.objects.get_or_create(name=name)[0]  # noqa: E731

        employers = []
        for i, (fn, ln, cname, cat, loc, tagline) in enumerate(EMPLOYERS, 1):
            u = service.register(email=f"employer{i}@{DOMAIN}", password=PASSWORD, first_name=fn, last_name=ln,
                                 role=User.Role.EMPLOYER, company_name=cname)
            Company.objects.filter(owner=u).update(industry=cats.get(cat), location=loc, tagline=tagline,
                                                   description=tagline + ". " + LOREM, size="11-50",
                                                   is_verified=i != 3, founded_year=2015 + i)
            employers.append(u)

        seekers = []
        for i, (fn, ln, headline, cat, years, skills, loc) in enumerate(SEEKERS, 1):
            u = service.register(email=f"seeker{i}@{DOMAIN}", password=PASSWORD, first_name=fn, last_name=ln,
                                 role=User.Role.SEEKER)
            p = u.profile
            p.headline, p.specialization, p.years_experience, p.location = headline, cats.get(cat), years, loc
            p.bio = f"{headline} بخبرة {years} سنوات. أحب حل المشكلات وبناء منتجات ذات أثر. (حساب تجريبي)"
            p.experience_level = "senior" if years >= 5 else "mid" if years >= 3 else "entry"
            p.hourly_rate = 10 + years * 5
            p.availability = random.choice(["available", "available", "open", "busy"])
            p.save()
            p.skills.set([skill(s) for s in skills])
            Experience.objects.create(profile=p, title=headline, company="شركة سابقة (تجريبي)",
                                      start_date=date.today() - timedelta(days=365 * years), is_current=True)
            for k in range(2):
                PortfolioItem.objects.create(profile=p, title=f"مشروع نموذجي {k + 1}", description="عمل تجريبي لعرض شكل معرض الأعمال.")
            seekers.append(u)

        jobs = []
        for i, (title, cat, wp, jt, lvl, smin, smax, skills) in enumerate(JOBS):
            owner = employers[i % len(employers)]
            job = Job.objects.create(
                company=owner.company, posted_by=owner, title=title, category=cats[cat], workplace=wp, job_type=jt,
                experience_level=lvl, salary_min=smin, salary_max=smax, location=owner.company.location,
                description=LOREM, responsibilities="تطوير وتحسين المنتج\nالتعاون مع الفريق\nكتابة توثيق واضح",
                requirements="خبرة مناسبة في المجال\nمهارات تواصل جيدة\nالقدرة على العمل ضمن فريق",
                benefits="تأمين صحي\nساعات عمل مرنة\nميزانية تعلم سنوية", is_featured=i < 2,
                deadline=date.today() + timedelta(days=30),
            )
            job.skills.set([skill(s) for s in skills])
            jobs.append(job)

        statuses = ["submitted", "reviewing", "shortlisted", "interview", "offered", "hired", "rejected"]
        for i, s in enumerate(seekers):
            for j in random.sample(jobs, 3):
                st = statuses[(i + j.pk) % len(statuses)]
                app = Application.objects.create(job=j, applicant=s, cover_letter="أرغب بالانضمام لفريقكم. (طلب تجريبي)", status=st)
                ApplicationEvent.objects.create(application=app, status="submitted", created_by=s)
                if st != "submitted":
                    ApplicationEvent.objects.create(application=app, status=st, created_by=j.company.owner)

        for i, (title, cat, bmin, bmax, days, skills) in enumerate(PROJECTS):
            owner = employers[i % len(employers)]
            pr = Project.objects.create(owner=owner, title=title, category=cats[cat], description=LOREM,
                                        deliverables="ملفات المصدر\nتوثيق التسليم", budget_min=bmin, budget_max=bmax,
                                        duration_days=days)
            pr.skills.set([skill(s) for s in skills])
            for s in random.sample(seekers, 3):
                Proposal.objects.create(project=pr, freelancer=s, cover_letter="لدي خبرة مشابهة ويمكنني التسليم في الوقت. (عرض تجريبي)",
                                        bid_amount=random.randint(bmin, bmax), delivery_days=days)
            if i == 0:  # one completed project with a verified review
                prop = pr.proposals.first()
                prop.status = "accepted"
                prop.save()
                pr.status, pr.freelancer = "completed", prop.freelancer
                pr.save()
                Review.objects.create(reviewer=owner, reviewee=prop.freelancer, project=pr, rating=5,
                                      comment="عمل ممتاز وتسليم في الموعد. (تقييم تجريبي)")

        for s in seekers[:3]:
            Testimonial.objects.create(author=s, role_title=s.profile.headline, rating=5, is_approved=True,
                                       content="تجربة سلسة وواجهة جميلة، وجدت فرصاً مناسبة بسرعة. (رأي تجريبي)")

        invalidate_stats()
        self.stdout.write(self.style.SUCCESS(
            f"Demo data created. Password for all demo accounts: {PASSWORD}\n"
            f"  admin@{DOMAIN}  |  employer1@{DOMAIN}  |  seeker1@{DOMAIN}"))
