from django.contrib import admin

from .models import Category, Job, SavedJob, Skill


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "name_en", "slug", "icon", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ("name_en",)}


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["title", "company", "category", "workplace", "status", "is_featured", "created_at"]
    list_filter = ["status", "workplace", "job_type", "category", "is_featured"]
    search_fields = ["title", "company__name"]
    autocomplete_fields = ["skills"]
    raw_id_fields = ["company", "posted_by"]


admin.site.register(SavedJob)
