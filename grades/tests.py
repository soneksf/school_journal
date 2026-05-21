from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import StudentProfile, TeacherProfile
from school_core.models import AcademicYear, SchoolClass, Subject

from .models import Grade

User = get_user_model()


class GradeModelTests(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025, 9, 1),
            end_date=date(2026, 5, 31), is_current=True,
        )
        self.cls = SchoolClass.objects.create(grade_level=10, letter="А", academic_year=self.year)
        self.subject = Subject.objects.create(name="Математика", short_code="МАТ")

        s_user = User.objects.create_user(username="stud", password="pw",
                                          role=User.Role.STUDENT,
                                          first_name="Олена", last_name="Коваль")
        self.student = s_user.student_profile
        self.student.school_class = self.cls
        self.student.save()

        t_user = User.objects.create_user(username="teach", password="pw",
                                          role=User.Role.TEACHER,
                                          first_name="Іван", last_name="Петренко")
        self.teacher = t_user.teacher_profile

    def test_grade_value_validators(self):
        g = Grade(student=self.student, subject=self.subject, teacher=self.teacher,
                  value=13, date=date.today())
        with self.assertRaises(ValidationError):
            g.full_clean()

    def test_excellent_flag(self):
        g = Grade.objects.create(student=self.student, subject=self.subject,
                                 teacher=self.teacher, value=11, date=date.today())
        self.assertTrue(g.is_excellent)
        self.assertFalse(g.is_unsatisfactory)
