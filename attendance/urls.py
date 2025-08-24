from django.urls import path
from .views import (
    take_attendance, mark_attendance, mark_attendance_custom, student_attendance,
    teacher_attendance_history, teacher_subject_attendance_history, teacher_attendance_detail,
    export_class_attendance, export_attendance_report,
)


urlpatterns = [
    path('attendance', take_attendance, name='take_attendance'),
    path("attendance/<int:subject_id>/<int:semester_id>/", mark_attendance, name="mark_attendance"),
    path("attendance/custom/", mark_attendance_custom, name="mark_attendance_custom"),

    path("attendance/history", teacher_attendance_history, name="teacher_attendance_history"),
    path("attendance/history/<int:subject_id>/<int:semester_id>/", teacher_subject_attendance_history, name="teacher_subject_attendance_history"),
    path("attendance/detail/<int:attendance_id>/", teacher_attendance_detail, name="teacher_attendance_detail"),
    path("attendance/export/session/<int:attendance_id>/", export_class_attendance, name="export_class_attendance"),
    path("attendance/export/", export_attendance_report, name="export_attendance_report"),

    path("attendance/", student_attendance, name="attendance"),
]
