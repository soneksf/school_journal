from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import AcademicYear, SchoolClass, Subject

User = get_user_model()


class SchoolClassTests(TestCase):
    def test_short_name_and_uniqueness(self):
        year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025, 9, 1), end_date=date(2026, 5, 31),
            is_current=True,
        )
        cls = SchoolClass.objects.create(grade_level=10, letter="А", academic_year=year)
        self.assertEqual(cls.short_name, "10-А")
        self.assertEqual(str(cls), "10-А")

    def test_only_one_current_year(self):
        y1 = AcademicYear.objects.create(name="2024-2025",
                                         start_date=date(2024, 9, 1),
                                         end_date=date(2025, 5, 31),
                                         is_current=True)
        y2 = AcademicYear.objects.create(name="2025-2026",
                                         start_date=date(2025, 9, 1),
                                         end_date=date(2026, 5, 31),
                                         is_current=True)
        y1.refresh_from_db()
        self.assertFalse(y1.is_current)
        self.assertTrue(y2.is_current)
