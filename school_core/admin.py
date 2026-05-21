from django.contrib import admin

from .models import AcademicYear, Lesson, SchoolClass, Subject, TeacherSubject


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_current")
    list_editable = ("is_current",)
    search_fields = ("name",)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("short_name", "academic_year", "homeroom_teacher")
    list_filter = ("academic_year", "grade_level")
    search_fields = ("letter",)
    autocomplete_fields = ("homeroom_teacher", "academic_year")


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "short_code")
    search_fields = ("name", "short_code")


@admin.register(TeacherSubject)
class TeacherSubjectAdmin(admin.ModelAdmin):
    list_display = ("teacher", "subject", "school_class")
    list_filter = ("subject", "school_class")
    autocomplete_fields = ("teacher", "school_class")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("date", "period_number", "school_class", "subject", "teacher", "topic")
    list_filter = ("school_class", "subject", "date")
    search_fields = ("topic",)
    date_hierarchy = "date"
    autocomplete_fields = ("school_class", "teacher")
