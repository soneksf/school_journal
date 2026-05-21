from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ParentProfile, StudentProfile, TeacherProfile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "full_name_uk", "role", "email", "phone", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "first_name", "last_name", "middle_name", "email")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Додаткові поля", {
            "fields": ("role", "middle_name", "phone", "birth_date", "avatar"),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Додаткові поля", {"fields": ("role", "email", "first_name", "last_name")}),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "employee_id", "specialization", "qualification_category")
    search_fields = ("user__last_name", "employee_id", "specialization")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "student_id", "school_class", "enrollment_date")
    list_filter = ("school_class",)
    search_fields = ("user__last_name", "student_id")
    autocomplete_fields = ("school_class",)


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "relation", "workplace")
    filter_horizontal = ("children",)
    search_fields = ("user__last_name",)
