def unread(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    from apps.messaging.models import Message

    return {
        "unread_notifications": user.notifications.filter(is_read=False).count(),
        "unread_messages": Message.objects.filter(conversation__participants=user, is_read=False)
        .exclude(sender=user).count(),
        "latest_notifications": user.notifications.all()[:5],
    }
