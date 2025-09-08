from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from college_portal.storage_backends import MediaStorage

class HOD(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hod_profile"
    )
    profile_image = models.ImageField(
        storage=MediaStorage(),
        upload_to="hod_profiles/", 
        blank=True, 
        null=True
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    employee_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    qualification = models.CharField(max_length=200, blank=True, null=True, help_text="Highest qualification (e.g., Ph.D in Electronics)")
    experience_years = models.PositiveIntegerField(blank=True, null=True, help_text="Total years of experience")
    joining_date = models.DateField(blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True, help_text="Area of expertise")
    office_address = models.TextField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True, help_text="Brief professional description")

    class Meta:
        verbose_name = "Head of Department"
        verbose_name_plural = "Heads of Department"

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
    def role(self):
        return getattr(self.user, "role", None)


# Automatically create HOD profile for new users with role="hod"
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_hod_profile(sender, instance, created, **kwargs):
    if created and getattr(instance, "role", None) == "hod":
        HOD.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_hod_profile(sender, instance, **kwargs):
    if getattr(instance, "role", None) == "hod" and hasattr(instance, "hod_profile"):
        instance.hod_profile.save()