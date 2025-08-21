from django.urls import path
from .views import take_attendance, mark_attendance, mark_attendance_custom, student_attendance


urlpatterns = [
    path('attendance', take_attendance, name='take_attendance'),
    path("attendance/<int:subject_id>/<int:semester_id>/", mark_attendance, name="mark_attendance"),
    path("attendance/custom/", mark_attendance_custom, name="mark_attendance_custom"),
    path("attendance/", student_attendance, name="attendance"),
]
