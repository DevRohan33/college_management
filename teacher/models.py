from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        limit_choices_to={'role': 'teacher'}
    )
    profile_image = models.ImageField(upload_to="teacher_profiles/", blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Requested fields
    degree = models.CharField(max_length=100, blank=True, null=True)
    primary_subject = models.CharField(max_length=100, blank=True, null=True)
    ability_subjects = models.TextField(blank=True, null=True, help_text="Comma-separated subjects you can teach")

    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"TeacherProfile({self.user.username})"

    @property
    def name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def department(self):
        return getattr(self.user, 'department', None)


# Auto-create/save profile for teachers
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_teacher_profile(sender, instance, created, **kwargs):
    if created and getattr(instance, 'role', None) == 'teacher':
        TeacherProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_teacher_profile(sender, instance, **kwargs):
    if getattr(instance, 'role', None) == 'teacher' and hasattr(instance, 'teacher_profile'):
        instance.teacher_profile.save()
