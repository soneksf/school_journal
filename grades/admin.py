from django.contrib import admin

from .models import Grade, GradePeriod


@admin.register(GradePeriod)
class GradePeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "academic_year", "kind", "start_date", "end_date", "is_open")
    list_filter = ("academic_year", "kind", "is_open")


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("date", "student", "subject", "value", "kind", "teacher")
    list_filter = ("subject", "kind", "date")
    search_fields = ("student__user__last_name", "comment")
    date_hierarchy = "date"
    autocomplete_fields = ("student", "subject", "teacher", "lesson")
