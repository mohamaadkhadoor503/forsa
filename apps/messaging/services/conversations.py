from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count
from django.urls import reverse
from django.utils.translation import gettext as _

from apps.messaging.models import Conversation, Message
from apps.notifications.models import Notification
from apps.notifications.services.notifier import DatabaseChannel, NotificationService


class ConversationService:
    def __init__(self, notifier: NotificationService | None = None):
        # Chat notifications stay in-app only to avoid e-mail spam.
        self.notifier = notifier or NotificationService([DatabaseChannel()])

    @staticmethod
    def between(user_a, user_b, subject=""):
        if user_a.pk == user_b.pk:
            raise PermissionDenied
        conv = (
            Conversation.objects.filter(participants=user_a).filter(participants=user_b)
            .annotate(n=Count("participants")).filter(n=2).first()
        )
        if conv:
            return conv
        conv = Conversation.objects.create(subject=subject)
        conv.participants.add(user_a, user_b)
        return conv

    @transaction.atomic
    def send(self, conversation, sender, body):
        if not conversation.participants.filter(pk=sender.pk).exists():
            raise PermissionDenied
        msg = Message.objects.create(conversation=conversation, sender=sender, body=body.strip())
        conversation.save(update_fields=["updated_at"])
        for other in conversation.participants.exclude(pk=sender.pk):
            self.notifier.notify(other, _("رسالة جديدة من %(n)s") % {"n": sender.display_name},
                                 body[:120], reverse("messaging:detail", args=[conversation.pk]),
                                 Notification.Kind.MESSAGE)
        return msg

    @staticmethod
    def mark_read(conversation, user):
        conversation.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
