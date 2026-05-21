from django import forms

from .models import Absence


class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ("student", "subject", "lesson", "date", "reason",
                  "is_excused", "note", "document")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher is not None:
            from accounts.models import StudentProfile
            from school_core.models import Subject, Lesson
            self.fields["student"].queryset = StudentProfile.objects.filter(
                school_class__teacher_assignments__teacher=teacher,
            ).distinct()
            self.fields["subject"].queryset = Subject.objects.filter(
                teacher_assignments__teacher=teacher,
            ).distinct()
            self.fields["lesson"].queryset = Lesson.objects.filter(teacher=teacher)
            self.fields["lesson"].required = False
