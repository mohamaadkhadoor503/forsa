from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import ListView

from .models import Notification
from .services.notifier import mark_all_read


class NotificationListView(LoginRequiredMixin, ListView):
    template_name = "dashboard/notifications.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class OpenNotificationView(LoginRequiredMixin, View):
    def post(self, request, pk):
        n = get_object_or_404(Notification, pk=pk, recipient=request.user)
        n.is_read = True
        n.save(update_fields=["is_read"])
        if n.url and url_has_allowed_host_and_scheme(n.url, {request.get_host()}):
            return redirect(n.url)
        return redirect("notifications:list")


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request):
        mark_all_read(request.user)
        return redirect("notifications:list")
