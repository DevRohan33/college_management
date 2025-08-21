from django.db import models
from django.conf import settings
from subject.models import Subject
from account.models import Department, Semester
from student.models import Student  


class Assignment(models.Model):
    title = models.CharField(max_length=200)
    details = models.TextField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments_created"
    )
    submit_last_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def submitted_students(self):
        """Return queryset of students who submitted"""
        return Student.objects.filter(submissions__assignment=self).distinct()

    def due_students(self):
        """Return students of same semester & department who did NOT submit"""
        return Student.objects.filter(
            user__semester=self.semester,
            user__department=self.department
        ).exclude(
            id__in=self.submissions.values_list("student_id", flat=True)
        )

    
    def is_active(self):
        """Check if submission is still allowed"""
        from django.utils import timezone
        return timezone.now() <= self.submit_last_date

    def __str__(self):
        return f"{self.title} - {self.subject.name} ({self.department.name}, {self.semester.semester})"


class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(
        Assignment, 
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    file = models.FileField(upload_to="assignments/submissions/")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} → {self.assignment.title}"

    # 🔹 Convenience properties
    @property
    def student_name(self):
        return self.student.name

    @property
    def registration_number(self):
        return self.student.registration_number

    @property
    def email(self):
        return self.student.email

    @property
    def mobile(self):
        return self.student.phone_number

    @property
    def semester(self):
        """Get semester from the linked User model"""
        return getattr(self.student.user, "semester", None)
