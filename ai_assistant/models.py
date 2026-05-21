"""AI-generated artifacts: per-student insights and support chat history."""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class StudentInsight(models.Model):
    """Anthropic-generated analysis of a student's performance."""

    class Status(models.TextChoices):
        PENDING = "pending", _("В обробці")
        READY = "ready", _("Готово")
        FAILED = "failed", _("Помилка")

    class Risk(models.TextChoices):
        LOW = "low", _("Низький")
        MEDIUM = "medium", _("Середній")
        HIGH = "high", _("Високий")
        UNKNOWN = "unknown", _("Невідомо")

    student = models.ForeignKey(
        "accounts.StudentProfile", on_delete=models.CASCADE, related_name="insights",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="requested_insights",
    )
    status = models.CharField(_("Статус"), max_length=16,
                              choices=Status.choices, default=Status.PENDING)
    risk_level = models.CharField(_("Рівень ризику"), max_length=16,
                                  choices=Risk.choices, default=Risk.UNKNOWN)
    summary = models.TextField(_("Короткий висновок"), blank=True)
    strengths = models.TextField(_("Сильні сторони"), blank=True)
    concerns = models.TextField(_("Зони уваги"), blank=True)
    recommendations = models.TextField(_("Рекомендації"), blank=True)
    raw_response = models.JSONField(_("Сирі дані"), default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("AI-аналіз учня")
        verbose_name_plural = _("AI-аналізи учнів")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Аналіз {self.student} — {self.get_status_display()}"


class ChatSession(models.Model):
    """A conversation with the AI support assistant."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions",
    )
    title = models.CharField(_("Тема"), max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Чат-сесія")
        verbose_name_plural = _("Чат-сесії")
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or f"Сесія #{self.pk}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", _("Користувач")
        ASSISTANT = "assistant", _("Асистент")
        SYSTEM = "system", _("Системне")

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Повідомлення чату")
        verbose_name_plural = _("Повідомлення чату")
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:60]}"
