"""Reusable mixins for role-based view protection."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restrict a view to one or more user roles."""

    allowed_roles: tuple[str, ...] = ()

    def test_func(self) -> bool:
        user = self.request.user
        return user.is_authenticated and (
            user.is_superuser or user.role in self.allowed_roles
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("Недостатньо прав для перегляду цієї сторінки.")
        return super().handle_no_permission()


class TeacherRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("teacher", "admin")


class StudentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("student",)


class ParentRequiredMixin(RoleRequiredMixin):
    allowed_roles = ("parent",)


class StaffOrTeacherMixin(RoleRequiredMixin):
    allowed_roles = ("teacher", "admin")
