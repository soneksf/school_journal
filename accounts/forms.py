"""User-facing forms."""
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import ParentProfile, StudentProfile, TeacherProfile, User


class RegistrationForm(UserCreationForm):
    """Self-service registration; admin creates teachers manually."""

    role = forms.ChoiceField(
        label="Роль",
        choices=[
            (User.Role.STUDENT, "Учень"),
            (User.Role.PARENT, "Батьки"),
        ],
    )

    class Meta:
        model = User
        fields = (
            "username", "first_name", "last_name", "middle_name",
            "email", "phone", "role",
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "middle_name", "email",
                  "phone", "birth_date", "avatar")
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"})}


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ("specialization", "qualification_category", "hired_at", "bio")
        widgets = {"hired_at": forms.DateInput(attrs={"type": "date"})}


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ("school_class", "enrollment_date", "address", "notes")
        widgets = {"enrollment_date": forms.DateInput(attrs={"type": "date"})}


class ParentProfileForm(forms.ModelForm):
    class Meta:
        model = ParentProfile
        fields = ("relation", "workplace", "children")
        widgets = {"children": forms.CheckboxSelectMultiple()}
