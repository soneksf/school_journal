"""Custom user with role-based access and role-specific profiles."""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Single user model differentiated by role."""

    class Role(models.TextChoices):
        ADMIN = "admin", _("Адміністратор")
        TEACHER = "teacher", _("Вчитель")
        STUDENT = "student", _("Учень")
        PARENT = "parent", _("Батьки")

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name=_("Роль"),
    )
    middle_name = models.CharField(_("По батькові"), max_length=80, blank=True)
    phone = models.CharField(_("Телефон"), max_length=32, blank=True)
    birth_date = models.DateField(_("Дата народження"), null=True, blank=True)
    avatar = models.ImageField(_("Фото"), upload_to="avatars/", null=True, blank=True)

    class Meta:
        verbose_name = _("Користувач")
        verbose_name_plural = _("Користувачі")
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        full = self.get_full_name() or self.username
        return f"{full} ({self.get_role_display()})"

    @property
    def is_teacher(self) -> bool:
        return self.role == self.Role.TEACHER

    @property
    def is_student(self) -> bool:
        return self.role == self.Role.STUDENT

    @property
    def is_parent(self) -> bool:
        return self.role == self.Role.PARENT

    @property
    def full_name_uk(self) -> str:
        """Surname Name Patronymic — Ukrainian academic style."""
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join(p for p in parts if p).strip() or self.username


class TeacherProfile(models.Model):
    """Profile data for users with the Teacher role."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="teacher_profile",
        limit_choices_to={"role": User.Role.TEACHER},
    )
    employee_id = models.CharField(_("Табельний номер"), max_length=32, unique=True)
    specialization = models.CharField(_("Спеціалізація"), max_length=120, blank=True)
    qualification_category = models.CharField(
        _("Категорія"),
        max_length=64,
        blank=True,
        help_text=_("Вища / Перша / Друга / Спеціаліст"),
    )
    hired_at = models.DateField(_("Дата прийняття"), null=True, blank=True)
    bio = models.TextField(_("Біографія"), blank=True)

    class Meta:
        verbose_name = _("Профіль вчителя")
        verbose_name_plural = _("Профілі вчителів")

    def __str__(self) -> str:
        return f"{self.user.full_name_uk} — {self.specialization or _('вчитель')}"

    def get_absolute_url(self) -> str:
        return reverse("accounts:teacher_detail", args=[self.pk])


class StudentProfile(models.Model):
    """Profile data for users with the Student role."""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile",
        limit_choices_to={"role": User.Role.STUDENT},
    )
    school_class = models.ForeignKey(
        "school_core.SchoolClass",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="students",
        verbose_name=_("Клас"),
    )
    enrollment_date = models.DateField(_("Дата зарахування"), null=True, blank=True)
    student_id = models.CharField(_("Особова справа №"), max_length=32, unique=True)
    address = models.CharField(_("Адреса"), max_length=255, blank=True)
    notes = models.TextField(_("Примітки"), blank=True)

    class Meta:
        verbose_name = _("Профіль учня")
        verbose_name_plural = _("Профілі учнів")
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self) -> str:
        cls = self.school_class.short_name if self.school_class else "—"
        return f"{self.user.full_name_uk} ({cls})"

    def get_absolute_url(self) -> str:
        return reverse("accounts:student_detail", args=[self.pk])


class ParentProfile(models.Model):
    """Profile data for users with the Parent role; linked to one or many students."""

    class Relation(models.TextChoices):
        MOTHER = "mother", _("Мати")
        FATHER = "father", _("Батько")
        GUARDIAN = "guardian", _("Опікун")
        OTHER = "other", _("Інше")

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="parent_profile",
        limit_choices_to={"role": User.Role.PARENT},
    )
    children = models.ManyToManyField(
        StudentProfile, related_name="parents", verbose_name=_("Діти"),
    )
    relation = models.CharField(
        _("Відношення"), max_length=16, choices=Relation.choices, default=Relation.OTHER
    )
    workplace = models.CharField(_("Місце роботи"), max_length=120, blank=True)
    contact_preferences = models.JSONField(
        _("Налаштування сповіщень"),
        default=dict, blank=True,
        help_text=_("Канали (email, sms, in_app) та події"),
    )

    class Meta:
        verbose_name = _("Профіль батьків")
        verbose_name_plural = _("Профілі батьків")

    def __str__(self) -> str:
        return f"{self.user.full_name_uk} — {self.get_relation_display()}"
