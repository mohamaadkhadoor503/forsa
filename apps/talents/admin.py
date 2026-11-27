from django.contrib import admin

from .models import Education, Experience, PortfolioItem, SeekerProfile


class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0


class PortfolioInline(admin.TabularInline):
    model = PortfolioItem
    extra = 0


@admin.register(SeekerProfile)
class SeekerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "headline", "specialization", "availability", "is_public"]
    list_filter = ["availability", "experience_level", "is_public"]
    search_fields = ["user__email", "user__first_name", "headline"]
    inlines = [ExperienceInline, PortfolioInline]
    raw_id_fields = ["user"]


admin.site.register(Education)
