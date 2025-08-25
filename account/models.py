from django.contrib.auth.models import AbstractUser
from django.db import models

# Each department (like CSE, ECE, IT, etc.)
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name


class Semester(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="batches")
    semester = models.IntegerField(null=True, blank=True)
    class Meta:
        unique_together = ('department', 'semester')
    def __str__(self):
        return f"Semester {self.semester} - ({self.department.name})"


# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('management', 'Management'),
        ('hod', 'Head of Department'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    semester = models.ForeignKey(Semester, on_delete=models.SET_NULL, null=True, blank=True) 

    # For Teachers — restrict to certain batches only
    accessible_batches = models.ManyToManyField(Semester, blank=True, related_name="teachers")

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        from django.utils.timezone import now
        return (now() - self.created_at).seconds < 300  # OTP valid for 5 minutes