"""Absence registration and listing."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from accounts.permissions import TeacherRequiredMixin
from notifications.services import notify_absence

from .forms import AbsenceForm
from .models import Absence


class AbsenceCreateView(TeacherRequiredMixin, CreateView):
    model = Absence
    form_class = AbsenceForm
    template_name = "attendance/absence_form.html"
    success_url = reverse_lazy("attendance:absence_list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not hasattr(request.user, "teacher_profile"):
            messages.error(
                request,
                "Фіксувати пропуски може лише користувач з профілем вчителя. "
                "Увійдіть під обліковим записом вчителя (наприклад teacher1 / demo12345).",
            )
            return redirect("attendance:absence_list")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user.teacher_profile
        return kwargs

    def form_valid(self, form):
        form.instance.recorded_by = self.request.user.teacher_profile
        response = super().form_valid(form)
        notify_absence.delay(self.object.pk)
        messages.success(self.request, "Пропуск зафіксовано. Сповіщення надіслано.")
        return response


class AbsenceUpdateView(TeacherRequiredMixin, UpdateView):
    model = Absence
    form_class = AbsenceForm
    template_name = "attendance/absence_form.html"
    success_url = reverse_lazy("attendance:absence_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["teacher"] = self.request.user.teacher_profile
        return kwargs


class AbsenceListView(LoginRequiredMixin, ListView):
    model = Absence
    template_name = "attendance/absence_list.html"
    context_object_name = "absences"
    paginate_by = 50

    def get_queryset(self):
        user = self.request.user
        qs = Absence.objects.select_related("student__user", "subject", "recorded_by__user")
        if user.is_teacher:
            qs = qs.filter(recorded_by=user.teacher_profile)
        elif user.is_student:
            qs = qs.filter(student=user.student_profile)
        elif user.is_parent:
            qs = qs.filter(student__in=user.parent_profile.children.all())
        return qs.order_by("-date")
