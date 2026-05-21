from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from school_core.models import AcademicYear, SchoolClass

from .models import Absence

User = get_user_model()


class AbsenceTests(TestCase):
    def test_create_absence(self):
        year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025, 9, 1),
            end_date=date(2026, 5, 31), is_current=True,
        )
        cls = SchoolClass.objects.create(grade_level=10, letter="А", academic_year=year)
        student_user = User.objects.create_user(
            username="s", password="pw", role=User.Role.STUDENT,
            first_name="Олена", last_name="Коваль",
        )
        student = student_user.student_profile
        student.school_class = cls
        student.save()

        a = Absence.objects.create(student=student, date=date.today(),
                                   reason=Absence.Reason.ILLNESS, is_excused=True)
        self.assertEqual(Absence.objects.count(), 1)
        self.assertIn("Хвороба", str(a))
