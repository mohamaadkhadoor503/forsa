"""Notification delivery.

``NotificationService`` depends on the ``NotificationChannel`` abstraction,
not on concrete delivery mechanisms. Adding SMS / push / websockets means
adding a channel class, not editing callers (Open/Closed + DIP).
"""
import logging
from typing import Iterable, Protocol

from django.conf import settings
from django.core.mail import send_mail

from apps.notifications.models import Notification

logger = logging.getLogger(__name__)


class NotificationChannel(Protocol):
    def send(self, recipient, title: str, body: str, url: str, kind: str) -> None: ...


class DatabaseChannel:
    def send(self, recipient, title, body, url, kind):
        Notification.objects.create(recipient=recipient, title=title, body=body, url=url, kind=kind)


class EmailChannel:
    def send(self, recipient, title, body, url, kind):
        if not getattr(recipient, "email_notifications", False) or not recipient.email:
            return
        try:
            send_mail(title, f"{body}\n\n{url}", settings.DEFAULT_FROM_EMAIL, [recipient.email], fail_silently=True)
        except Exception:  # never break the main flow because of e-mail
            logger.exception("email notification failed")


class NotificationService:
    def __init__(self, channels: Iterable[NotificationChannel] | None = None):
        self.channels = list(channels) if channels is not None else [DatabaseChannel(), EmailChannel()]

    def notify(self, recipient, title, body="", url="", kind=Notification.Kind.INFO):
        for channel in self.channels:
            channel.send(recipient, str(title), str(body), url, kind)


def mark_all_read(user):
    return Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)
