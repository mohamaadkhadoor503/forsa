from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


def unique_slug(model, value, max_length=200):
    base = slugify(value, allow_unicode=True)[: max_length - 8] or "item"
    slug, i = base, 1
    while model.objects.filter(slug=slug).exists():
        i += 1
        slug = f"{base}-{i}"
    return slug


class Category(models.Model):
    name = models.CharField(_("الاسم"), max_length=80)
    name_en = models.CharField(_("الاسم (إنجليزي)"), max_length=80, blank=True)
    slug = models.SlugField(_("المعرّف"), unique=True, allow_unicode=True)
    icon = models.CharField(_("الأيقونة"), max_length=30, default="briefcase")
    color = models.CharField(_("اللون"), max_length=9, default="#2563EB")
    order = models.PositiveSmallIntegerField(_("الترتيب"), default=0)
    is_active = models.BooleanField(_("مفعّل"), default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("تصنيف")
        verbose_name_plural = _("التصنيفات")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("jobs:list") + f"?category={self.slug}"


class Skill(models.Model):
    name = models.CharField(_("المهارة"), max_length=60, unique=True)
    slug = models.SlugField(unique=True, allow_unicode=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("مهارة")
        verbose_name_plural = _("المهارات")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Skill, self.name, 60)
        super().save(*args, **kwargs)


class Workplace(models.TextChoices):
    REMOTE = "remote", _("عن بعد")
    ONSITE = "onsite", _("حضوري")
    HYBRID = "hybrid", _("هجين")


class ExperienceLevel(models.TextChoices):
    ENTRY = "entry", _("مبتدئ")
    MID = "mid", _("متوسط")
    SENIOR = "senior", _("خبير")
    LEAD = "lead", _("قيادي")


class JobQuerySet(models.QuerySet):
    def published(self):
        now = timezone.now()
        return self.filter(status=Job.Status.PUBLISHED).filter(
            models.Q(deadline__isnull=True) | models.Q(deadline__gte=now.date())
        )

    def with_relations(self):
        return self.select_related("company", "category").prefetch_related("skills")


class Job(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", _("مسودة")
        PENDING = "pending", _("بانتظار المراجعة")
        PUBLISHED = "published", _("منشورة")
        CLOSED = "closed", _("مغلقة")

    class JobType(models.TextChoices):
        FULL_TIME = "full_time", _("دوام كامل")
        PART_TIME = "part_time", _("دوام جزئي")
        CONTRACT = "contract", _("عقد")
        INTERNSHIP = "internship", _("تدريب")
        FREELANCE = "freelance", _("عمل حر")

    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE, related_name="jobs", verbose_name=_("الشركة"))
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="posted_jobs")
    title = models.CharField(_("المسمى الوظيفي"), max_length=160)
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="jobs", verbose_name=_("التخصص"))
    description = models.TextField(_("وصف الوظيفة"))
    responsibilities = models.TextField(_("المسؤوليات"), blank=True, help_text=_("سطر لكل مسؤولية"))
    requirements = models.TextField(_("المتطلبات"), blank=True, help_text=_("سطر لكل متطلب"))
    benefits = models.TextField(_("المزايا"), blank=True, help_text=_("سطر لكل ميزة"))
    location = models.CharField(_("الموقع"), max_length=120)
    workplace = models.CharField(_("طبيعة العمل"), max_length=10, choices=Workplace.choices, default=Workplace.ONSITE, db_index=True)
    job_type = models.CharField(_("نوع الوظيفة"), max_length=12, choices=JobType.choices, default=JobType.FULL_TIME, db_index=True)
    experience_level = models.CharField(_("مستوى الخبرة"), max_length=10, choices=ExperienceLevel.choices, default=ExperienceLevel.MID, db_index=True)
    salary_min = models.PositiveIntegerField(_("الراتب الأدنى"), null=True, blank=True)
    salary_max = models.PositiveIntegerField(_("الراتب الأعلى"), null=True, blank=True)
    currency = models.CharField(_("العملة"), max_length=5, default="$")
    skills = models.ManyToManyField(Skill, blank=True, related_name="jobs", verbose_name=_("المهارات المطلوبة"))
    status = models.CharField(_("الحالة"), max_length=10, choices=Status.choices, default=Status.PUBLISHED, db_index=True)
    is_featured = models.BooleanField(_("مميزة"), default=False)
    deadline = models.DateField(_("آخر موعد للتقديم"), null=True, blank=True)
    views_count = models.PositiveIntegerField(default=0)

    objects = JobQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("وظيفة")
        verbose_name_plural = _("الوظائف")
        indexes = [models.Index(fields=["status", "-created_at"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Job, self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("jobs:detail", args=[self.slug])

    @property
    def salary_display(self):
        if self.salary_min and self.salary_max:
            return f"{self.currency}{self.salary_min:,} – {self.currency}{self.salary_max:,}"
        if self.salary_min:
            return f"{self.currency}{self.salary_min:,}+"
        return ""

    @property
    def is_open(self):
        return self.status == self.Status.PUBLISHED and (self.deadline is None or self.deadline >= timezone.now().date())


class SavedJob(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "job")
        ordering = ["-created_at"]
        verbose_name = _("وظيفة محفوظة")
        verbose_name_plural = _("الوظائف المحفوظة")
