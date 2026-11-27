from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("", views.ProjectListView.as_view(), name="list"),
    path("proposal/<int:pk>/withdraw/", views.WithdrawProposalView.as_view(), name="withdraw_proposal"),
    path("proposal/<int:pk>/<str:action>/", views.ProposalActionView.as_view(), name="proposal_action"),
    path("manage/<int:pk>/<str:action>/", views.ProjectStatusView.as_view(), name="status"),
    path("<str:slug>/", views.ProjectDetailView.as_view(), name="detail"),
    path("<str:slug>/propose/", views.SubmitProposalView.as_view(), name="propose"),
]
