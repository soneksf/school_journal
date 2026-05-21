"""Background AI analysis tasks."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from celery import shared_task
from django.utils import timezone as djtz

from .client import AnthropicError, parse_json_response, send_messages
from .models import StudentInsight

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """Ти — асистент шкільного класного керівника в Україні.
Аналізуєш академічну успішність та відвідуваність одного учня.
Відповідь ПОВИННА бути лише JSON-обʼєктом без жодного тексту до або після.
Структура JSON:
{
  "risk_level": "low" | "medium" | "high",
  "summary": "1-2 речення українською",
  "strengths": "перелік сильних сторін",
  "concerns": "перелік проблемних місць",
  "recommendations": "практичні поради для вчителя та батьків"
}
Бал 1-3 = незадовільно, 4-6 = задовільно, 7-9 = добре, 10-12 = відмінно.
Якщо даних недостатньо — risk_level = "low" та поясни в summary.
"""


def _build_student_payload(insight: StudentInsight) -> str:
    """Compose a compact textual dataset for the model."""
    student = insight.student
    grades = list(
        student.grades.select_related("subject")
        .order_by("-date")[:40]
        .values("date", "subject__name", "value", "kind")
    )
    absences = list(
        student.absences.select_related("subject")
        .order_by("-date")[:30]
        .values("date", "subject__name", "reason", "is_excused")
    )

    lines = [
        f"Учень: {student.user.full_name_uk}",
        f"Клас: {student.school_class.short_name if student.school_class else '—'}",
        "",
        "Оцінки (останні 40):",
    ]
    if grades:
        for g in grades:
            lines.append(
                f"  {g['date']} | {g['subject__name']:20s} | {g['value']:>2} ({g['kind']})"
            )
    else:
        lines.append("  немає")

    lines.append("")
    lines.append("Пропуски (останні 30):")
    if absences:
        for a in absences:
            excused = "поважна" if a["is_excused"] else "неповажна"
            lines.append(
                f"  {a['date']} | {a['subject__name'] or '—':20s} | {a['reason']} ({excused})"
            )
    else:
        lines.append("  немає")

    return "\n".join(lines)


@shared_task(name="ai_assistant.generate_student_insight", bind=True, max_retries=2)
def generate_student_insight(self, insight_id: int) -> str:
    """Populate a StudentInsight by querying the Anthropic API."""
    try:
        insight = StudentInsight.objects.select_related("student__user").get(pk=insight_id)
    except StudentInsight.DoesNotExist:
        logger.warning("Insight %s missing", insight_id)
        return "missing"

    insight.status = StudentInsight.Status.PENDING
    insight.save(update_fields=["status"])

    payload = _build_student_payload(insight)
    user_message = (
        "Проаналізуй наступні дані учня та поверни структурований JSON-висновок.\n\n"
        + payload
    )

    try:
        text = send_messages(
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=1500,
            temperature=0.2,
        )
        data = parse_json_response(text)
    except AnthropicError as exc:
        insight.status = StudentInsight.Status.FAILED
        insight.error_message = str(exc)
        insight.completed_at = djtz.now()
        insight.save()
        logger.error("Insight %s failed: %s", insight_id, exc)
        return "failed"

    insight.risk_level = data.get("risk_level", "unknown")
    insight.summary = data.get("summary", "")
    insight.strengths = data.get("strengths", "")
    insight.concerns = data.get("concerns", "")
    insight.recommendations = data.get("recommendations", "")
    insight.raw_response = data
    insight.status = StudentInsight.Status.READY
    insight.completed_at = djtz.now()
    insight.save()

    # Notify the teacher / homeroom teacher that analysis is ready.
    from notifications.services import broadcast_announcement  # avoid circular
    from notifications.tasks import _push
    if insight.requested_by:
        _push(
            recipient=insight.requested_by,
            kind="ai_summary",
            title=f"AI-аналіз готовий: {insight.student.user.full_name_uk}",
            body=insight.summary or "Звіт сформовано, перегляньте деталі.",
            url=f"/ai/insights/{insight.pk}/",
            related_type="student_insight",
            related_id=insight.pk,
        )
    return "ready"


@shared_task(name="ai_assistant.chat_reply")
def chat_reply(session_id: int) -> str:
    """Generate a reply for the most recent user message in a chat session."""
    from .models import ChatMessage, ChatSession

    try:
        session = ChatSession.objects.get(pk=session_id)
    except ChatSession.DoesNotExist:
        return "missing"

    history = list(session.messages.order_by("created_at"))
    if not history or history[-1].role != ChatMessage.Role.USER:
        return "no-user-message"

    api_messages = [
        {"role": m.role, "content": m.content}
        for m in history if m.role in (ChatMessage.Role.USER, ChatMessage.Role.ASSISTANT)
    ]
    system = (
        "Ти — ввічливий шкільний асистент. Відповідай українською стисло "
        "(2-5 речень). Не вигадуй конкретні оцінки або події."
    )

    try:
        text = send_messages(system=system, messages=api_messages,
                             max_tokens=600, temperature=0.5)
    except AnthropicError as exc:
        text = f"Вибачте, сервіс наразі недоступний: {exc}"

    ChatMessage.objects.create(session=session, role=ChatMessage.Role.ASSISTANT, content=text)
    return "ok"
