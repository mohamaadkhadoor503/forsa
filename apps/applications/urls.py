from django.urls import path

from . import views

app_name = "applications"

urlpatterns = [
    path("apply/<str:slug>/", views.ApplyView.as_view(), name="apply"),
    path("<int:pk>/withdraw/", views.WithdrawApplicationView.as_view(), name="withdraw"),
    path("<int:pk>/status/", views.ChangeApplicationStatusView.as_view(), name="change_status"),
]
