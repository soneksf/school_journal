"""Auto-create the appropriate profile when a user is saved."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ParentProfile, StudentProfile, TeacherProfile, User


@receiver(post_save, sender=User)
def create_role_profile(sender, instance: User, created: bool, **kwargs):
    """Best-effort profile bootstrap when admin creates a user."""
    if not created:
        return

    if instance.role == User.Role.TEACHER and not hasattr(instance, "teacher_profile"):
        TeacherProfile.objects.create(
            user=instance,
            employee_id=f"T-{instance.pk:06d}",
        )
    elif instance.role == User.Role.STUDENT and not hasattr(instance, "student_profile"):
        StudentProfile.objects.create(
            user=instance,
            student_id=f"S-{instance.pk:06d}",
        )
    elif instance.role == User.Role.PARENT and not hasattr(instance, "parent_profile"):
        ParentProfile.objects.create(user=instance)
