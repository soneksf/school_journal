"""In-app notifications stored in DB plus optional email delivery."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class Kind(models.TextChoices):
        GRADE = "grade", _("Оцінка")
        ABSENCE = "absence", _("Пропуск")
        ANNOUNCEMENT = "announcement", _("Оголошення")
        AI_SUMMARY = "ai_summary", _("AI-звіт")
        SYSTEM = "system", _("Системне")

    class Channel(models.TextChoices):
        IN_APP = "in_app", _("У застосунку")
        EMAIL = "email", _("Email")

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(_("Тип"), max_length=16, choices=Kind.choices, default=Kind.SYSTEM)
    channel = models.CharField(_("Канал"), max_length=16, choices=Channel.choices,
                               default=Channel.IN_APP)
    title = models.CharField(_("Заголовок"), max_length=200)
    body = models.TextField(_("Текст"))
    related_object_type = models.CharField(_("Тип обʼєкту"), max_length=40, blank=True)
    related_object_id = models.PositiveIntegerField(_("ID обʼєкту"), null=True, blank=True)
    url = models.CharField(_("Посилання"), max_length=255, blank=True)
    is_read = models.BooleanField(_("Прочитано"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(_("Відправлено"), null=True, blank=True)

    class Meta:
        verbose_name = _("Сповіщення")
        verbose_name_plural = _("Сповіщення")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"[{self.get_kind_display()}] {self.title}"

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=["is_read"])
