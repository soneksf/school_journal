"""Grade entry, listing, and student report views."""
from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Count, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.models import StudentProfile
from accounts.permissions import TeacherRequiredMixin
from notifications.services import notify_grade

from .forms import GradeForm
from .models import Grade


class GradeCreateView(TeacherRequiredMixin, CreateView):
    model = Grade
    form_class = GradeForm
    template_name = "grades/grade_form.html"
    success_url = reverse_lazy("grades:grade_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not hasattr(request.user, "teacher_profile"):
            messages.error(
                request,
                "Виставляти оцінки може лише користувач з профілем вчителя. "
                "Увійдіть під обліковим записом вчителя (наприклад teacher1 / demo12345).",
            )
            return redirect("grades:grade_list")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        # Fire async notifications to student & parents.
        notify_grade.delay(self.object.pk)
        messages.success(self.request, "Оцінку додано. Сповіщення надіслано.")
        return response


class GradeUpdateView(TeacherRequiredMixin, UpdateView):
    model = Grade
    form_class = GradeForm
    template_name = "grades/grade_form.html"
    success_url = reverse_lazy("grades:grade_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user.teacher_profile
        return kwargs

    def get_queryset(self):
        # Teachers may only edit their own grades.
        return Grade.objects.filter(teacher=self.request.user.teacher_profile)


class GradeListView(LoginRequiredMixin, ListView):
    """List of grades scoped per role."""

    model = Grade
    template_name = "grades/grade_list.html"
    context_object_name = "grades"
    paginate_by = 50

    def get_queryset(self):
        user = self.request.user
        qs = Grade.objects.select_related(
            "student__user", "subject", "teacher__user", "lesson")
        if user.is_teacher:
            qs = qs.filter(teacher=user.teacher_profile)
        elif user.is_student:
            qs = qs.filter(student=user.student_profile)
        elif user.is_parent:
            qs = qs.filter(student__in=user.parent_profile.children.all())
        return qs.order_by("-date")


@login_required
def student_report(request, student_id: int):
    """Per-student grade report grouped by subject."""
    student = get_object_or_404(StudentProfile, pk=student_id)
    user = request.user

    # Authorization: student themself, their parent, any teacher, or admin.
    can_view = (
        user.is_superuser
        or user.is_teacher
        or (user.is_student and user.student_profile_id == student.pk)
        or (user.is_parent and user.parent_profile.children.filter(pk=student.pk).exists())
    )
    if not can_view:
        return HttpResponseForbidden("Доступ заборонено")

    grades = (
        Grade.objects.filter(student=student)
        .select_related("subject", "teacher__user")
        .order_by("subject__name", "date")
    )

    by_subject = defaultdict(list)
    for g in grades:
        by_subject[g.subject].append(g)

    summary = []
    for subject, items in by_subject.items():
        values = [g.value for g in items]
        summary.append({
            "subject": subject,
            "grades": items,
            "avg": round(sum(values) / len(values), 2) if values else None,
            "count": len(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        })
    summary.sort(key=lambda s: s["subject"].name)

    overall_avg = (
        grades.aggregate(a=Avg("value"))["a"] if grades.exists() else None
    )

    return render(request, "grades/student_report.html", {
        "student": student,
        "summary": summary,
        "overall_avg": round(overall_avg, 2) if overall_avg else None,
        "total": grades.count(),
    })
