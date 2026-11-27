from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.InboxView.as_view(), name="inbox"),
    path("<int:pk>/", views.InboxView.as_view(), name="detail"),
    path("<int:pk>/send/", views.SendMessageView.as_view(), name="send"),
    path("<int:pk>/poll/", views.PollMessagesView.as_view(), name="poll"),
    path("start/<int:user_id>/", views.StartConversationView.as_view(), name="start"),
]
