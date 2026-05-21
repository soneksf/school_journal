"""Core academic entities: classes, subjects, lessons."""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class AcademicYear(models.Model):
    name = models.CharField(_("Навчальний рік"), max_length=20, unique=True,
                            help_text="напр. 2025-2026")
    start_date = models.DateField(_("Початок"))
    end_date = models.DateField(_("Кінець"))
    is_current = models.BooleanField(_("Поточний"), default=False)

    class Meta:
        verbose_name = _("Навчальний рік")
        verbose_name_plural = _("Навчальні роки")
        ordering = ["-start_date"]

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class SchoolClass(models.Model):
    """A class group (e.g. '10-А')."""

    grade_level = models.PositiveSmallIntegerField(
        _("Паралель"), help_text="1..11")
    letter = models.CharField(_("Літера"), max_length=2, default="А")
    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.PROTECT, related_name="classes",
        verbose_name=_("Навчальний рік"),
    )
    homeroom_teacher = models.ForeignKey(
        "accounts.TeacherProfile",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="homeroom_classes",
        verbose_name=_("Класний керівник"),
    )

    class Meta:
        verbose_name = _("Клас")
        verbose_name_plural = _("Класи")
        unique_together = ("grade_level", "letter", "academic_year")
        ordering = ["grade_level", "letter"]

    def __str__(self) -> str:
        return self.short_name

    @property
    def short_name(self) -> str:
        return f"{self.grade_level}-{self.letter}"

    @property
    def name(self) -> str:
        return f"{self.short_name} ({self.academic_year.name})"

    def get_absolute_url(self) -> str:
        return reverse("school_core:class_detail", args=[self.pk])


class Subject(models.Model):
    name = models.CharField(_("Назва предмету"), max_length=80, unique=True)
    short_code = models.CharField(_("Скорочення"), max_length=8, blank=True)
    description = models.TextField(_("Опис"), blank=True)

    class Meta:
        verbose_name = _("Предмет")
        verbose_name_plural = _("Предмети")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TeacherSubject(models.Model):
    """Which teacher teaches which subject to which class."""

    teacher = models.ForeignKey(
        "accounts.TeacherProfile", on_delete=models.CASCADE,
        related_name="teaching_assignments",
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE,
                                related_name="teacher_assignments")
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE,
        related_name="teacher_assignments",
    )

    class Meta:
        verbose_name = _("Призначення вчителя")
        verbose_name_plural = _("Призначення вчителів")
        unique_together = ("teacher", "subject", "school_class")

    def __str__(self) -> str:
        return f"{self.teacher.user.full_name_uk} — {self.subject} ({self.school_class})"


class Lesson(models.Model):
    """A concrete lesson event (used to anchor grades and absences)."""

    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name="lessons",
    )
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="lessons")
    teacher = models.ForeignKey(
        "accounts.TeacherProfile", on_delete=models.PROTECT, related_name="lessons",
    )
    date = models.DateField(_("Дата"))
    period_number = models.PositiveSmallIntegerField(
        _("№ уроку"), default=1, help_text="Порядковий номер уроку в розкладі")
    topic = models.CharField(_("Тема уроку"), max_length=255, blank=True)
    homework = models.TextField(_("Домашнє завдання"), blank=True)

    class Meta:
        verbose_name = _("Урок")
        verbose_name_plural = _("Уроки")
        ordering = ["-date", "period_number"]
        indexes = [
            models.Index(fields=["school_class", "date"]),
            models.Index(fields=["teacher", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.subject} — {self.school_class} ({self.date})"
