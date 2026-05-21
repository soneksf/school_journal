"""Grading models — Ukrainian 12-point scale."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class GradePeriod(models.Model):
    """Reporting period (term / semester / year)."""

    class Kind(models.TextChoices):
        TERM = "term", _("Семестр")
        QUARTER = "quarter", _("Чверть")
        YEAR = "year", _("Річна")

    academic_year = models.ForeignKey(
        "school_core.AcademicYear", on_delete=models.CASCADE, related_name="grade_periods",
    )
    name = models.CharField(_("Назва періоду"), max_length=64)
    kind = models.CharField(_("Тип"), max_length=16, choices=Kind.choices, default=Kind.TERM)
    start_date = models.DateField(_("Початок"))
    end_date = models.DateField(_("Кінець"))
    is_open = models.BooleanField(_("Відкритий для оцінювання"), default=True)

    class Meta:
        verbose_name = _("Період оцінювання")
        verbose_name_plural = _("Періоди оцінювання")
        ordering = ["academic_year", "start_date"]

    def __str__(self) -> str:
        return f"{self.name} ({self.academic_year.name})"


class Grade(models.Model):
    """A single mark put by a teacher to a student for a subject."""

    class Kind(models.TextChoices):
        CURRENT = "current", _("Поточна")
        CONTROL = "control", _("Контрольна")
        HOMEWORK = "homework", _("Домашня")
        ORAL = "oral", _("Усна відповідь")
        FINAL = "final", _("Підсумкова")

    student = models.ForeignKey(
        "accounts.StudentProfile", on_delete=models.CASCADE, related_name="grades",
    )
    subject = models.ForeignKey(
        "school_core.Subject", on_delete=models.PROTECT, related_name="grades",
    )
    teacher = models.ForeignKey(
        "accounts.TeacherProfile", on_delete=models.PROTECT, related_name="grades_given",
    )
    lesson = models.ForeignKey(
        "school_core.Lesson", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="grades",
    )
    period = models.ForeignKey(
        GradePeriod, on_delete=models.PROTECT, null=True, blank=True, related_name="grades",
    )
    value = models.PositiveSmallIntegerField(
        _("Бал"),
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text=_("12-бальна шкала"),
    )
    kind = models.CharField(_("Тип оцінки"), max_length=16, choices=Kind.choices,
                            default=Kind.CURRENT)
    date = models.DateField(_("Дата"))
    comment = models.CharField(_("Коментар"), max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Оцінка")
        verbose_name_plural = _("Оцінки")
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["student", "subject", "date"]),
            models.Index(fields=["teacher", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.student} — {self.subject}: {self.value}"

    @property
    def is_excellent(self) -> bool:
        return self.value >= 10

    @property
    def is_unsatisfactory(self) -> bool:
        return self.value <= 3
