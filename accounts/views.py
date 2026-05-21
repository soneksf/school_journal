"""Authentication and profile views."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from .forms import (
    ParentProfileForm, RegistrationForm, StudentProfileForm,
    TeacherProfileForm, UserProfileForm,
)
from .models import ParentProfile, StudentProfile, TeacherProfile, User
from .permissions import StaffOrTeacherMixin


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Реєстрація успішна. Заповніть профіль.")
            return redirect("accounts:profile_edit")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_edit(request):
    user = request.user
    user_form = UserProfileForm(request.POST or None, request.FILES or None, instance=user)

    role_form = None
    if user.is_teacher and hasattr(user, "teacher_profile"):
        role_form = TeacherProfileForm(request.POST or None, instance=user.teacher_profile)
    elif user.is_student and hasattr(user, "student_profile"):
        role_form = StudentProfileForm(request.POST or None, instance=user.student_profile)
    elif user.is_parent and hasattr(user, "parent_profile"):
        role_form = ParentProfileForm(request.POST or None, instance=user.parent_profile)

    if request.method == "POST":
        user_ok = user_form.is_valid()
        role_ok = role_form is None or role_form.is_valid()
        if user_ok and role_ok:
            user_form.save()
            if role_form:
                role_form.save()
            messages.success(request, "Профіль збережено.")
            return redirect("accounts:profile_edit")

    return render(request, "accounts/profile_edit.html",
                  {"user_form": user_form, "role_form": role_form})


class StudentListView(StaffOrTeacherMixin, ListView):
    model = StudentProfile
    template_name = "accounts/student_list.html"
    context_object_name = "students"
    paginate_by = 30

    def get_queryset(self):
        qs = (
            StudentProfile.objects
            .select_related("user", "school_class")
            .order_by("school_class__grade_level", "school_class__letter",
                      "user__last_name")
        )
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(user__last_name__icontains=q)
        cls = self.request.GET.get("class")
        if cls:
            qs = qs.filter(school_class_id=cls)
        return qs


class StudentDetailView(LoginRequiredMixin, DetailView):
    model = StudentProfile
    template_name = "accounts/student_detail.html"
    context_object_name = "student"

    def get_context_data(self, **kwargs):
        from attendance.models import Absence
        from grades.models import Grade
        ctx = super().get_context_data(**kwargs)
        student = self.object
        ctx["grades"] = (
            Grade.objects.filter(student=student)
            .select_related("subject", "teacher__user").order_by("-date")[:20]
        )
        ctx["absences"] = (
            Absence.objects.filter(student=student)
            .select_related("subject").order_by("-date")[:20]
        )
        return ctx


class TeacherListView(StaffOrTeacherMixin, ListView):
    model = TeacherProfile
    template_name = "accounts/teacher_list.html"
    context_object_name = "teachers"
    paginate_by = 30

    def get_queryset(self):
        return TeacherProfile.objects.select_related("user").order_by("user__last_name")


class TeacherDetailView(LoginRequiredMixin, DetailView):
    model = TeacherProfile
    template_name = "accounts/teacher_detail.html"
    context_object_name = "teacher"
