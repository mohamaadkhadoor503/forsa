from django.contrib import messages as flash
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic import TemplateView

from .models import Conversation
from .services.conversations import ConversationService


def user_conversations(user):
    return (
        Conversation.objects.filter(participants=user)
        .prefetch_related("participants")
        .annotate(unread=Count("messages", filter=Q(messages__is_read=False) & ~Q(messages__sender=user)))
    )


class InboxView(LoginRequiredMixin, TemplateView):
    template_name = "messaging/inbox.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["conversations"] = user_conversations(user)
        pk = self.kwargs.get("pk")
        ctx["active"] = None
        if pk:
            conv = get_object_or_404(Conversation.objects.filter(participants=user), pk=pk)
            ConversationService.mark_read(conv, user)
            ctx["active"] = conv
            ctx["thread"] = conv.messages.select_related("sender")
            ctx["other"] = conv.other(user)
        return ctx


class StartConversationView(LoginRequiredMixin, View):
    def post(self, request, user_id):
        other = get_object_or_404(get_user_model(), pk=user_id, is_active=True)
        if other.pk == request.user.pk:
            return redirect("messaging:inbox")
        conv = ConversationService.between(request.user, other, request.POST.get("subject", "")[:160])
        body = (request.POST.get("body") or "").strip()
        if body:
            ConversationService().send(conv, request.user, body)
        return redirect("messaging:detail", pk=conv.pk)


class SendMessageView(LoginRequiredMixin, View):
    def post(self, request, pk):
        conv = get_object_or_404(Conversation.objects.filter(participants=request.user), pk=pk)
        body = (request.POST.get("body") or "").strip()
        if not body:
            flash.error(request, _("لا يمكن إرسال رسالة فارغة."))
            return redirect("messaging:detail", pk=pk)
        msg = ConversationService().send(conv, request.user, body[:4000])
        if request.headers.get("X-Requested-With") == "fetch":
            return JsonResponse(_serialize(msg, request.user))
        return redirect("messaging:detail", pk=pk)


class PollMessagesView(LoginRequiredMixin, View):
    def get(self, request, pk):
        conv = get_object_or_404(Conversation.objects.filter(participants=request.user), pk=pk)
        after = int(request.GET.get("after") or 0)
        new = conv.messages.filter(pk__gt=after).select_related("sender")
        data = [_serialize(m, request.user) for m in new]
        ConversationService.mark_read(conv, request.user)
        return JsonResponse({"messages": data})


def _serialize(msg, user):
    return {
        "id": msg.pk,
        "body": msg.body,
        "mine": msg.sender_id == user.pk,
        "time": timezone.localtime(msg.created_at).strftime("%H:%M"),
    }
