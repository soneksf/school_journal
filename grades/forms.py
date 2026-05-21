from django import forms

from .models import Grade


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ("student", "subject", "lesson", "period",
                  "value", "kind", "date", "comment")
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "comment": forms.TextInput(),
        }

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._teacher = teacher
        if teacher is not None:
            from accounts.models import StudentProfile
            from school_core.models import Subject, Lesson
            self.fields["student"].queryset = StudentProfile.objects.filter(
                school_class__teacher_assignments__teacher=teacher
            ).distinct()
            self.fields["subject"].queryset = Subject.objects.filter(
                teacher_assignments__teacher=teacher
            ).distinct()
            self.fields["lesson"].queryset = Lesson.objects.filter(teacher=teacher)
            self.fields["lesson"].required = False

    def save(self, commit=True):
        obj = super().save(commit=False)
        if self._teacher is not None:
            obj.teacher = self._teacher
        if commit:
            obj.save()
        return obj


class GradeFilterForm(forms.Form):
    student = forms.IntegerField(required=False, widget=forms.HiddenInput)
    subject = forms.IntegerField(required=False, widget=forms.HiddenInput)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
