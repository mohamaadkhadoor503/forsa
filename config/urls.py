from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core.sitemaps import sitemaps

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("accounts/", include("apps.accounts.urls")),
    path("jobs/", include("apps.jobs.urls")),
    path("projects/", include("apps.projects.urls")),
    path("companies/", include("apps.companies.urls")),
    path("talents/", include("apps.talents.urls")),
    path("applications/", include("apps.applications.urls")),
    path("messages/", include("apps.messaging.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", include("apps.core.urls")),
]

handler403 = "apps.core.views.errors.permission_denied"
handler404 = "apps.core.views.errors.page_not_found"
handler500 = "apps.core.views.errors.server_error"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
