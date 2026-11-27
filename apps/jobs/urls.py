from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    path("", views.JobListView.as_view(), name="list"),
    path("<str:slug>/", views.JobDetailView.as_view(), name="detail"),
    path("<str:slug>/save/", views.ToggleSaveJobView.as_view(), name="toggle_save"),
]
