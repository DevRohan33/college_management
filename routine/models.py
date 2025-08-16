from django.db import models
from account.models import Department, Semester
from subject.models import Subject

class ClassRoutine(models.Model):
    DAYS = [
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday')
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='routines')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='routines')
    day_of_week = models.CharField(max_length=3, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='routines')

    def __str__(self):
        return f"{self.department.name} - Semester {self.semester.semester} - {self.get_day_of_week_display()} ({self.subject.name})"
