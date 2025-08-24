from django.db import models
from django.conf import settings
from account.models import Department, Semester
from subject.models import Subject


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    taken_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject.name} - {self.department.name} - {self.semester.semester} - {self.date}"


class AttendanceEntry(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='entries')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Attendance.STATUS_CHOICES)
    marked_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} - {self.attendance.subject.name} ({self.status})"