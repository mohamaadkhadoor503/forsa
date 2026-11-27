from django.contrib import admin

from .models import Company, FavoriteTalent


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "industry", "location", "is_verified", "is_featured"]
    list_filter = ["is_verified", "is_featured", "industry"]
    list_editable = ["is_verified", "is_featured"]
    search_fields = ["name", "owner__email"]
    raw_id_fields = ["owner"]


admin.site.register(FavoriteTalent)
