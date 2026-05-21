"""Absence tracking."""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Absence(models.Model):
    """Single recorded absence at a lesson."""

    class Reason(models.TextChoices):
        ILLNESS = "illness", _("Хвороба")
        FAMILY = "family", _("Сімейні обставини")
        COMPETITION = "competition", _("Олімпіада/змагання")
        UNEXCUSED = "unexcused", _("Без поважної причини")
        OTHER = "other", _("Інше")

    student = models.ForeignKey(
        "accounts.StudentProfile", on_delete=models.CASCADE, related_name="absences",
    )
    lesson = models.ForeignKey(
        "school_core.Lesson", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="absences",
    )
    subject = models.ForeignKey(
        "school_core.Subject", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="absences",
    )
    date = models.DateField(_("Дата"))
    reason = models.CharField(
        _("Причина"), max_length=16, choices=Reason.choices, default=Reason.UNEXCUSED,
    )
    is_excused = models.BooleanField(_("Поважна"), default=False)
    note = models.CharField(_("Коментар"), max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        "accounts.TeacherProfile", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="recorded_absences",
    )
    document = models.FileField(_("Довідка"), upload_to="absences/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Пропуск")
        verbose_name_plural = _("Пропуски")
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["student", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} — {self.date} ({self.get_reason_display()})"
