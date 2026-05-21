"""Tests for the accounts app."""
from django.test import TestCase
from django.urls import reverse

from .models import ParentProfile, StudentProfile, TeacherProfile, User


class UserRoleTests(TestCase):
    def test_role_helpers(self):
        u = User.objects.create_user(username="s1", password="pw", role=User.Role.STUDENT)
        self.assertTrue(u.is_student)
        self.assertFalse(u.is_teacher)

    def test_profile_autocreated_on_user_creation(self):
        teacher = User.objects.create_user(
            username="t1", password="pw", role=User.Role.TEACHER,
            first_name="Іван", last_name="Петренко",
        )
        self.assertTrue(TeacherProfile.objects.filter(user=teacher).exists())

        student = User.objects.create_user(
            username="s2", password="pw", role=User.Role.STUDENT,
        )
        self.assertTrue(StudentProfile.objects.filter(user=student).exists())

        parent = User.objects.create_user(
            username="p1", password="pw", role=User.Role.PARENT,
        )
        self.assertTrue(ParentProfile.objects.filter(user=parent).exists())

    def test_full_name_uk(self):
        u = User.objects.create_user(
            username="x", password="pw",
            first_name="Софія", last_name="Бивалькевич", middle_name="Андріївна",
        )
        self.assertEqual(u.full_name_uk, "Бивалькевич Софія Андріївна")


class AuthViewsTests(TestCase):
    def test_login_page_renders(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)

    def test_protected_redirects_anonymous(self):
        resp = self.client.get(reverse("accounts:profile_edit"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)
