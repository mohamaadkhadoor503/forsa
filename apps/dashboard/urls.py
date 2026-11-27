from django.urls import path

from apps.messaging.views import InboxView
from apps.notifications.views import NotificationListView

from .views import common, employer, seeker, staff

app_name = "dashboard"

urlpatterns = [
    path("", common.DashboardHomeRedirect.as_view(), name="home"),
    path("settings/", common.AccountSettingsView.as_view(), name="settings"),
    path("messages/", InboxView.as_view(), name="messages"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),

    # Seeker
    path("me/", seeker.SeekerHomeView.as_view(), name="seeker_home"),
    path("me/profile/", seeker.SeekerProfileEditView.as_view(), name="seeker_profile"),
    path("me/cv/", seeker.SeekerCVView.as_view(), name="seeker_cv"),
    path("me/portfolio/", seeker.PortfolioView.as_view(), name="seeker_portfolio"),
    path("me/experience/", seeker.ExperienceView.as_view(), name="seeker_experience"),
    path("me/delete/<str:kind>/<int:pk>/", seeker.DeleteProfileItemView.as_view(), name="seeker_delete_item"),
    path("me/recommended/", seeker.RecommendedJobsView.as_view(), name="seeker_recommended"),
    path("me/applications/", seeker.SeekerApplicationsView.as_view(), name="seeker_applications"),
    path("me/proposals/", seeker.SeekerProposalsView.as_view(), name="seeker_proposals"),
    path("me/saved/", seeker.SavedJobsView.as_view(), name="seeker_saved"),

    # Employer
    path("company/", employer.EmployerHomeView.as_view(), name="employer_home"),
    path("company/profile/", employer.CompanyEditView.as_view(), name="employer_company"),
    path("company/jobs/", employer.EmployerJobsView.as_view(), name="employer_jobs"),
    path("company/jobs/new/", employer.JobCreateView.as_view(), name="employer_job_create"),
    path("company/jobs/<int:pk>/edit/", employer.JobUpdateView.as_view(), name="employer_job_edit"),
    path("company/jobs/<int:pk>/applications/", employer.JobApplicationsView.as_view(), name="employer_job_applications"),
    path("company/applications/", employer.JobApplicationsView.as_view(), name="employer_applications"),
    path("company/projects/", employer.EmployerProjectsView.as_view(), name="employer_projects"),
    path("company/projects/new/", employer.ProjectCreateView.as_view(), name="employer_project_create"),
    path("company/projects/<int:pk>/edit/", employer.ProjectUpdateView.as_view(), name="employer_project_edit"),
    path("company/projects/<int:pk>/proposals/", employer.ProjectProposalsView.as_view(), name="employer_project_proposals"),
    path("company/favorites/", employer.FavoritesView.as_view(), name="employer_favorites"),

    # Platform admin
    path("admin/", staff.AdminHomeView.as_view(), name="admin_home"),
    path("admin/users/", staff.AdminUsersView.as_view(), name="admin_users"),
    path("admin/companies/", staff.AdminCompaniesView.as_view(), name="admin_companies"),
    path("admin/jobs/", staff.AdminJobsView.as_view(), name="admin_jobs"),
    path("admin/projects/", staff.AdminProjectsView.as_view(), name="admin_projects"),
    path("admin/categories/", staff.AdminCategoriesView.as_view(), name="admin_categories"),
    path("admin/categories/new/", staff.CategoryCreateView.as_view(), name="admin_category_create"),
    path("admin/categories/<int:pk>/", staff.CategoryUpdateView.as_view(), name="admin_category_edit"),
    path("admin/reports/", staff.AdminReportsView.as_view(), name="admin_reports"),
    path("admin/content/", staff.AdminContentView.as_view(), name="admin_content"),
    path("admin/settings/", staff.AdminSettingsView.as_view(), name="admin_settings"),
    path("admin/action/<str:action>/<int:pk>/", staff.AdminActionView.as_view(), name="admin_action"),
]
