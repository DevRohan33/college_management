from django.db import models
from django.conf import settings
from account.models import Department, Semester
from subject.models import Subject


class ExamSession(models.Model):
    EXAM_TYPES = [
        ("CA1", "CA1"),
        ("CA2", "CA2"),
        ("CA3", "CA3"),
        ("CA4", "CA4"),
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="exam_sessions")
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="exam_sessions")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="exam_sessions")

    exam_type = models.CharField(max_length=10, choices=EXAM_TYPES)
    full_marks = models.PositiveIntegerField(default=25)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="locked_exam_sessions")

    class Meta:
        unique_together = ("department", "semester", "subject", "exam_type")

    def __str__(self):
        return f"{self.exam_type} - {self.subject.name} (Sem {self.semester.semester})"


class ExamMark(models.Model):
    session = models.ForeignKey(ExamSession, on_delete=models.CASCADE, related_name="marks")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={"role": "student"})
    marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ("session", "student")

    def __str__(self):
        return f"{self.student} - {self.session}: {self.marks}"


class StudentSGPA(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={"role": "student"})
    semester_num = models.PositiveSmallIntegerField()  # 1..8
    sgpa = models.DecimalField(max_digits=4, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "semester_num")
        ordering = ("semester_num",)

    def __str__(self):
        return f"{self.student} - Sem {self.semester_num}: {self.sgpa}"
