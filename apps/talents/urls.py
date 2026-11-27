from django.urls import path

from . import views

app_name = "talents"

urlpatterns = [
    path("", views.TalentListView.as_view(), name="list"),
    path("<int:pk>/", views.TalentDetailView.as_view(), name="detail"),
    path("<int:pk>/favorite/", views.ToggleFavoriteTalentView.as_view(), name="toggle_favorite"),
]
