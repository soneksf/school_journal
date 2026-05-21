"""Inject unread-count into every template."""
from .models import Notification


def unread_notifications(request):
    if not request.user.is_authenticated:
        return {"unread_notifications": 0}
    count = Notification.objects.filter(
        recipient=request.user,
        channel=Notification.Channel.IN_APP,
        is_read=False,
    ).count()
    return {"unread_notifications": count}
