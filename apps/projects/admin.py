from django.contrib import admin

from .models import Project, Proposal


class ProposalInline(admin.TabularInline):
    model = Proposal
    extra = 0
    raw_id_fields = ["freelancer"]


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "category", "budget_min", "budget_max", "status", "created_at"]
    list_filter = ["status", "category", "budget_type"]
    search_fields = ["title"]
    inlines = [ProposalInline]
    raw_id_fields = ["owner", "freelancer"]
