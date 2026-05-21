"""Views for AI student insights and chat assistant."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView

from accounts.models import StudentProfile
from accounts.permissions import TeacherRequiredMixin

from .models import ChatMessage, ChatSession, StudentInsight
from .tasks import chat_reply, generate_student_insight


class InsightListView(TeacherRequiredMixin, ListView):
    model = StudentInsight
    template_name = "ai_assistant/insight_list.html"
    context_object_name = "insights"
    paginate_by = 30

    def get_queryset(self):
        return (
            StudentInsight.objects
            .select_related("student__user", "requested_by")
            .order_by("-created_at")
        )


class InsightDetailView(LoginRequiredMixin, DetailView):
    model = StudentInsight
    template_name = "ai_assistant/insight_detail.html"
    context_object_name = "insight"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = request.user
        student = self.object.student
        allowed = (
            user.is_superuser
            or user.is_teacher
            or (user.is_student and user.student_profile_id == student.pk)
            or (user.is_parent and user.parent_profile.children.filter(pk=student.pk).exists())
        )
        if not allowed:
            return HttpResponseForbidden("Доступ заборонено")
        return super().get(request, *args, **kwargs)


@login_required
def request_insight(request, student_id: int):
    """Teacher triggers an async AI analysis for a single student."""
    if not (request.user.is_teacher or request.user.is_superuser):
        return HttpResponseForbidden("Лише вчитель може запитати AI-аналіз")

    student = get_object_or_404(StudentProfile, pk=student_id)
    insight = StudentInsight.objects.create(
        student=student,
        requested_by=request.user,
        status=StudentInsight.Status.PENDING,
    )
    generate_student_insight.delay(insight.pk)
    messages.success(request, "Запит на AI-аналіз надіслано. Результат зʼявиться невдовзі.")
    return redirect("ai_assistant:insight_detail", pk=insight.pk)


@login_required
def chat_view(request, session_id: int | None = None):
    """Simple chat interface backed by Anthropic."""
    if session_id:
        session = get_object_or_404(ChatSession, pk=session_id, user=request.user)
    else:
        session = None

    if request.method == "POST":
        text = request.POST.get("message", "").strip()
        if not text:
            messages.error(request, "Введіть повідомлення")
            return redirect(request.path)

        if session is None:
            session = ChatSession.objects.create(
                user=request.user, title=text[:80],
            )
        ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=text,
        )
        chat_reply.delay(session.pk)
        return redirect("ai_assistant:chat", session_id=session.pk)

    history = session.messages.all() if session else []
    sessions = ChatSession.objects.filter(user=request.user)[:20]
    return render(request, "ai_assistant/chat.html", {
        "session": session, "history": history, "sessions": sessions,
    })
