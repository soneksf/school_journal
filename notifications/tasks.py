"""Async notification tasks.

Calling sites use `notify_grade.delay(grade_id)` / `notify_absence.delay(absence_id)`.
Celery worker picks the job up and dispatches both in-app and email notifications
to the student and any parents.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

logger = logging.getLogger(__name__)


def _send_email(notification) -> bool:
    """Send an email; tolerate misconfigured environment in dev."""
    try:
        send_mail(
            subject=notification.title,
            message=notification.body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[notification.recipient.email],
            fail_silently=False,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Email send failed for notification %s: %s", notification.pk, exc)
        return False


def _push(*, recipient, kind, title, body, url="", related_type="", related_id=None):
    from .models import Notification

    in_app = Notification.objects.create(
        recipient=recipient, kind=kind,
        channel=Notification.Channel.IN_APP,
        title=title, body=body, url=url,
        related_object_type=related_type, related_object_id=related_id,
    )

    # Email duplicate, if the user has an email address.
    if recipient.email:
        email_n = Notification.objects.create(
            recipient=recipient, kind=kind,
            channel=Notification.Channel.EMAIL,
            title=title, body=body, url=url,
            related_object_type=related_type, related_object_id=related_id,
        )
        if _send_email(email_n):
            email_n.sent_at = datetime.now(timezone.utc)
            email_n.save(update_fields=["sent_at"])
    return in_app


@shared_task(name="notifications.notify_grade")
def notify_grade(grade_id: int) -> int:
    """Notify the student and their parents that a new grade was added."""
    from grades.models import Grade

    try:
        grade = Grade.objects.select_related(
            "student__user", "subject", "teacher__user"
        ).get(pk=grade_id)
    except Grade.DoesNotExist:
        logger.warning("notify_grade: Grade %s not found", grade_id)
        return 0

    student = grade.student
    teacher_name = grade.teacher.user.full_name_uk
    title = f"Нова оцінка з предмета «{grade.subject}»"
    body = (
        f"Учень: {student.user.full_name_uk}\n"
        f"Предмет: {grade.subject}\n"
        f"Бал: {grade.value} ({grade.get_kind_display()})\n"
        f"Дата: {grade.date.strftime('%d.%m.%Y')}\n"
        f"Вчитель: {teacher_name}\n"
        f"Коментар: {grade.comment or '—'}"
    )
    url = reverse("grades:student_report", args=[student.pk])

    sent = 0
    recipients = {student.user, *(p.user for p in student.parents.select_related("user"))}
    for rcpt in recipients:
        _push(recipient=rcpt, kind="grade", title=title, body=body, url=url,
              related_type="grade", related_id=grade.pk)
        sent += 1
    return sent


@shared_task(name="notifications.notify_absence")
def notify_absence(absence_id: int) -> int:
    from attendance.models import Absence

    try:
        a = Absence.objects.select_related("student__user", "subject").get(pk=absence_id)
    except Absence.DoesNotExist:
        logger.warning("notify_absence: Absence %s not found", absence_id)
        return 0

    student = a.student
    title = f"Пропуск занять {a.date.strftime('%d.%m.%Y')}"
    subj_name = a.subject.name if a.subject else "—"
    body = (
        f"Учень: {student.user.full_name_uk}\n"
        f"Предмет: {subj_name}\n"
        f"Причина: {a.get_reason_display()}\n"
        f"Поважна: {'так' if a.is_excused else 'ні'}\n"
        f"Коментар: {a.note or '—'}"
    )
    url = reverse("attendance:absence_list")

    sent = 0
    recipients = {student.user, *(p.user for p in student.parents.select_related("user"))}
    for rcpt in recipients:
        _push(recipient=rcpt, kind="absence", title=title, body=body, url=url,
              related_type="absence", related_id=a.pk)
        sent += 1
    return sent


@shared_task(name="notifications.broadcast_announcement")
def broadcast_announcement(title: str, body: str, role: str | None = None) -> int:
    """Send a system announcement; optionally limited to a single role."""
    from accounts.models import User

    qs = User.objects.filter(is_active=True)
    if role:
        qs = qs.filter(role=role)

    count = 0
    for user in qs.iterator():
        _push(recipient=user, kind="announcement", title=title, body=body)
        count += 1
    return count
