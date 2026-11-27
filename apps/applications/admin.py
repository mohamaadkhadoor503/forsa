from django.contrib import admin

from .models import Application, ApplicationEvent


class EventInline(admin.TabularInline):
    model = ApplicationEvent
    extra = 0


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["applicant", "job", "status", "created_at"]
    list_filter = ["status"]
    inlines = [EventInline]
    raw_id_fields = ["job", "applicant"]
