from django.contrib import admin
from .models import ExamSession, ExamMark

@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ("exam_type", "subject", "semester", "department", "locked")
    list_filter = ("exam_type", "department", "semester", "locked")

@admin.register(ExamMark)
class ExamMarkAdmin(admin.ModelAdmin):
    list_display = ("session", "student", "marks")
    search_fields = ("student__username", "student__first_name", "student__last_name")
    list_filter = ("session__exam_type",)
