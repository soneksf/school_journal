"""Populate the database with realistic demo data for quick evaluation."""
import random
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import ParentProfile, StudentProfile, TeacherProfile
from attendance.models import Absence
from grades.models import Grade, GradePeriod
from school_core.models import AcademicYear, Lesson, SchoolClass, Subject, TeacherSubject

User = get_user_model()

UA_FIRST_NAMES_F = ["Софія", "Анастасія", "Марія", "Катерина", "Олена", "Ірина", "Дарина", "Юлія"]
UA_FIRST_NAMES_M = ["Іван", "Андрій", "Олег", "Максим", "Богдан", "Дмитро", "Ярослав", "Тарас"]
UA_LAST_NAMES = ["Шевченко", "Коваль", "Бондаренко", "Ткаченко", "Петренко",
                 "Іваненко", "Мельник", "Гончар", "Кравчук", "Левченко",
                 "Поліщук", "Савченко", "Лисенко", "Романенко", "Олійник"]


class Command(BaseCommand):
    help = "Заповнює базу демо-даними: класи, предмети, користувачі, оцінки, пропуски."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Видалити існуючі демо-обʼєкти перед створенням.")

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(42)

        if options["reset"]:
            self.stdout.write("Видалення попередніх демо-даних...")
            Grade.objects.all().delete()
            Absence.objects.all().delete()
            Lesson.objects.all().delete()
            TeacherSubject.objects.all().delete()
            StudentProfile.objects.exclude(user__is_superuser=True).delete()
            TeacherProfile.objects.exclude(user__is_superuser=True).delete()
            ParentProfile.objects.exclude(user__is_superuser=True).delete()
            User.objects.exclude(is_superuser=True).delete()

        self.stdout.write("Створення академічного року...")
        year, _ = AcademicYear.objects.get_or_create(
            name="2025-2026",
            defaults={
                "start_date": date(2025, 9, 1),
                "end_date": date(2026, 5, 31),
                "is_current": True,
            },
        )

        GradePeriod.objects.get_or_create(
            academic_year=year, name="І семестр",
            defaults={"kind": "term", "start_date": date(2025, 9, 1),
                      "end_date": date(2025, 12, 28), "is_open": True},
        )
        GradePeriod.objects.get_or_create(
            academic_year=year, name="ІІ семестр",
            defaults={"kind": "term", "start_date": date(2026, 1, 15),
                      "end_date": date(2026, 5, 31), "is_open": True},
        )

        self.stdout.write("Створення предметів...")
        subject_data = [
            ("Українська мова", "УМ"), ("Українська література", "УЛ"),
            ("Математика", "МАТ"), ("Алгебра", "АЛГ"), ("Геометрія", "ГЕО"),
            ("Англійська мова", "АНГ"), ("Історія України", "ІСТ"),
            ("Біологія", "БІО"), ("Хімія", "ХІМ"), ("Фізика", "ФІЗ"),
            ("Інформатика", "ІНФ"), ("Фізична культура", "ФК"),
        ]
        subjects = []
        for name, code in subject_data:
            s, _ = Subject.objects.get_or_create(name=name, defaults={"short_code": code})
            subjects.append(s)

        self.stdout.write("Створення вчителів...")
        teachers = []
        for i in range(6):
            first = random.choice(UA_FIRST_NAMES_F + UA_FIRST_NAMES_M)
            last = random.choice(UA_LAST_NAMES)
            uname = f"teacher{i+1}"
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    "first_name": first, "last_name": last,
                    "middle_name": "Олегівна" if first in UA_FIRST_NAMES_F else "Олегович",
                    "email": f"{uname}@school.local", "role": User.Role.TEACHER,
                },
            )
            if created:
                u.set_password("demo12345")
                u.save()
            tp = u.teacher_profile
            tp.specialization = random.choice(["Математика", "Українська філологія",
                                               "Природничі науки", "Іноземні мови",
                                               "Історія та суспільствознавство", "Фізкультура"])
            tp.qualification_category = random.choice(["Вища", "Перша", "Друга", "Спеціаліст"])
            tp.hired_at = date(2018, 9, 1) + timedelta(days=random.randint(0, 1500))
            tp.save()
            teachers.append(tp)

        self.stdout.write("Створення класів...")
        classes = []
        for grade_level in (9, 10, 11):
            for letter in ("А", "Б"):
                cls, _ = SchoolClass.objects.get_or_create(
                    grade_level=grade_level, letter=letter, academic_year=year,
                    defaults={"homeroom_teacher": random.choice(teachers)},
                )
                classes.append(cls)

        self.stdout.write("Призначення вчителів на предмети та класи...")
        for cls in classes:
            for subject in random.sample(subjects, k=8):
                TeacherSubject.objects.get_or_create(
                    teacher=random.choice(teachers), subject=subject, school_class=cls,
                )

        self.stdout.write("Створення учнів...")
        students = []
        for cls in classes:
            for i in range(random.randint(12, 18)):
                first_pool = UA_FIRST_NAMES_F if i % 2 == 0 else UA_FIRST_NAMES_M
                first = random.choice(first_pool)
                last = random.choice(UA_LAST_NAMES)
                uname = f"student_{cls.short_name.replace('-', '')}_{i+1}".replace("А", "A").replace("Б", "B")
                u, created = User.objects.get_or_create(
                    username=uname,
                    defaults={
                        "first_name": first, "last_name": last,
                        "email": f"{uname}@school.local", "role": User.Role.STUDENT,
                    },
                )
                if created:
                    u.set_password("demo12345")
                    u.save()
                sp = u.student_profile
                sp.school_class = cls
                sp.enrollment_date = date(2015 + (17 - cls.grade_level), 9, 1)
                sp.save()
                students.append(sp)

        self.stdout.write("Створення батьків...")
        for sp in students[:30]:
            uname = f"parent_{sp.user.username}"
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    "first_name": "Олена" if random.random() > 0.5 else "Петро",
                    "last_name": sp.user.last_name,
                    "email": f"{uname}@parent.local", "role": User.Role.PARENT,
                },
            )
            if created:
                u.set_password("demo12345")
                u.save()
            pp = u.parent_profile
            pp.relation = ParentProfile.Relation.MOTHER if random.random() > 0.5 else ParentProfile.Relation.FATHER
            pp.save()
            pp.children.add(sp)

        self.stdout.write("Створення уроків та оцінок (це може зайняти 10-20 секунд)...")
        today = date.today()
        for cls in classes:
            assignments = TeacherSubject.objects.filter(school_class=cls).select_related("subject", "teacher")
            for assignment in assignments:
                for d in range(0, 60, 7):  # ~9 уроків за останні 2 місяці
                    lesson_date = today - timedelta(days=d)
                    lesson, _ = Lesson.objects.get_or_create(
                        school_class=cls, subject=assignment.subject,
                        teacher=assignment.teacher,
                        date=lesson_date,
                        period_number=random.randint(1, 6),
                        defaults={"topic": f"Тема {random.randint(1, 30)}"},
                    )
                    for sp in cls.students.all():
                        if random.random() < 0.55:
                            Grade.objects.create(
                                student=sp, subject=assignment.subject,
                                teacher=assignment.teacher, lesson=lesson,
                                value=random.choices(
                                    range(1, 13),
                                    weights=[1, 1, 2, 3, 5, 7, 10, 12, 14, 16, 15, 14],
                                )[0],
                                kind=random.choice(["current", "oral", "homework"]),
                                date=lesson_date,
                            )

        self.stdout.write("Створення пропусків...")
        for sp in random.sample(students, k=min(40, len(students))):
            for _ in range(random.randint(1, 4)):
                Absence.objects.create(
                    student=sp,
                    date=today - timedelta(days=random.randint(1, 60)),
                    subject=random.choice(subjects),
                    reason=random.choice(["illness", "family", "unexcused", "competition"]),
                    is_excused=random.random() > 0.4,
                    recorded_by=random.choice(teachers),
                )

        self.stdout.write(self.style.SUCCESS(
            f"Готово! Створено: {len(teachers)} вчителів, {len(classes)} класів, "
            f"{len(students)} учнів, {Grade.objects.count()} оцінок, "
            f"{Absence.objects.count()} пропусків."
        ))
        self.stdout.write("Логін будь-якого користувача: пароль demo12345")
        self.stdout.write("  Приклад вчителя: teacher1")
        self.stdout.write("  Приклад учня: student_9A_1")
