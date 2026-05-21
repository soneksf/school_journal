from django.contrib import admin

from .models import Absence


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ("date", "student", "subject", "reason", "is_excused", "recorded_by")
    list_filter = ("reason", "is_excused", "date")
    search_fields = ("student__user__last_name", "note")
    date_hierarchy = "date"
    autocomplete_fields = ("student", "subject", "lesson", "recorded_by")
