"""Dashboard and core academic views."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from accounts.permissions import StaffOrTeacherMixin

from .models import Lesson, SchoolClass, Subject


@login_required
def dashboard(request):
    """Role-dispatching landing page."""
    user = request.user
    ctx = {"user": user, "today": timezone.localdate()}

    if user.is_teacher and hasattr(user, "teacher_profile"):
        ctx["my_classes"] = (
            SchoolClass.objects
            .filter(teacher_assignments__teacher=user.teacher_profile)
            .distinct()
        )
        ctx["recent_lessons"] = (
            Lesson.objects.filter(teacher=user.teacher_profile)
            .select_related("subject", "school_class").order_by("-date")[:10]
        )
        return render(request, "school_core/dashboard_teacher.html", ctx)

    if user.is_student and hasattr(user, "student_profile"):
        from grades.models import Grade
        from attendance.models import Absence
        student = user.student_profile
        ctx["student"] = student
        ctx["recent_grades"] = (
            Grade.objects.filter(student=student)
            .select_related("subject", "teacher__user").order_by("-date")[:10]
        )
        ctx["recent_absences"] = (
            Absence.objects.filter(student=student)
            .select_related("subject").order_by("-date")[:10]
        )
        return render(request, "school_core/dashboard_student.html", ctx)

    if user.is_parent and hasattr(user, "parent_profile"):
        ctx["children"] = user.parent_profile.children.select_related(
            "user", "school_class")
        return render(request, "school_core/dashboard_parent.html", ctx)

    return render(request, "school_core/dashboard_admin.html", ctx)


class ClassListView(StaffOrTeacherMixin, ListView):
    model = SchoolClass
    template_name = "school_core/class_list.html"
    context_object_name = "classes"

    def get_queryset(self):
        return (
            SchoolClass.objects.select_related("academic_year", "homeroom_teacher__user")
            .order_by("grade_level", "letter")
        )


class ClassDetailView(LoginRequiredMixin, DetailView):
    model = SchoolClass
    template_name = "school_core/class_detail.html"
    context_object_name = "school_class"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["students"] = self.object.students.select_related("user").order_by(
            "user__last_name")
        ctx["subjects"] = Subject.objects.filter(
            teacher_assignments__school_class=self.object
        ).distinct()
        return ctx


class SubjectListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = "school_core/subject_list.html"
    context_object_name = "subjects"
