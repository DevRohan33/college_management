from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from college_portal.storage_backends import MediaStorage


class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    profile_image = models.ImageField(
        storage=MediaStorage(),
        upload_to="student_profiles/", 
        blank=True, 
        null=True
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    session = models.CharField(max_length=20, blank=True, null=True)
    aap_id = models.CharField(max_length=50, blank=True, null=True)
    registration_number = models.CharField(max_length=50, blank=True, null=True)
    roll_no = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"

    @property
    def name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def department(self):
        return getattr(self.user, "department", None)

    @property
    def semester(self):
        return getattr(self.user, "semester", None)


# Automatically create Student profile for new users with role="student"
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_student_profile(sender, instance, created, **kwargs):
    if created and getattr(instance, "role", None) == "student":
        Student.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_student_profile(sender, instance, **kwargs):
    if getattr(instance, "role", None) == "student" and hasattr(instance, "student_profile"):
        instance.student_profile.save()

