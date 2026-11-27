from django.contrib import admin

from .models import Report, Review, Testimonial


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["reviewer", "reviewee", "project", "rating", "created_at"]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["author", "role_title", "rating", "is_approved", "created_at"]
    list_editable = ["is_approved"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["target_type", "target_label", "reason", "status", "reporter", "created_at"]
    list_filter = ["status", "reason", "target_type"]
