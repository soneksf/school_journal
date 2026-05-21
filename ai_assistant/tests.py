"""Tests for ai_assistant — Anthropic client is monkey-patched."""
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from school_core.models import AcademicYear, SchoolClass

from .models import StudentInsight
from .tasks import generate_student_insight

User = get_user_model()


class InsightTaskTests(TestCase):
    def setUp(self):
        year = AcademicYear.objects.create(
            name="2025-2026", start_date=date(2025, 9, 1),
            end_date=date(2026, 5, 31), is_current=True,
        )
        cls = SchoolClass.objects.create(grade_level=10, letter="А", academic_year=year)
        u = User.objects.create_user(username="s", password="pw", role=User.Role.STUDENT,
                                     first_name="Олена", last_name="Коваль")
        self.student = u.student_profile
        self.student.school_class = cls
        self.student.save()

    @patch("ai_assistant.tasks.send_messages")
    def test_generate_insight_success(self, mock_send):
        mock_send.return_value = (
            '{"risk_level": "medium", "summary": "Стабільний учень",'
            ' "strengths": "математика", "concerns": "пропуски",'
            ' "recommendations": "поговорити з батьками"}'
        )
        insight = StudentInsight.objects.create(student=self.student)
        generate_student_insight(insight.pk)
        insight.refresh_from_db()
        self.assertEqual(insight.status, StudentInsight.Status.READY)
        self.assertEqual(insight.risk_level, "medium")
        self.assertIn("Стабільний", insight.summary)

    @patch("ai_assistant.tasks.send_messages")
    def test_generate_insight_failure(self, mock_send):
        from .client import AnthropicError
        mock_send.side_effect = AnthropicError("network down")
        insight = StudentInsight.objects.create(student=self.student)
        generate_student_insight(insight.pk)
        insight.refresh_from_db()
        self.assertEqual(insight.status, StudentInsight.Status.FAILED)
        self.assertIn("network down", insight.error_message)
