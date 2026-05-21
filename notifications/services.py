"""Public service API for notifications.

Other apps should import `notify_grade` / `notify_absence` from here so the
implementation (currently Celery) can be swapped without changing call sites.
"""
from .tasks import broadcast_announcement, notify_absence, notify_grade

__all__ = ("notify_grade", "notify_absence", "broadcast_announcement")
