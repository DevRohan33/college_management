from django.urls import path
from .views import (
    teacher_profile_view,
    teacher_students_list,
    teacher_student_detail,
)

urlpatterns = [
    path('profile/', teacher_profile_view, name='teacher_profile'),
    path('students/', teacher_students_list, name='teacher_students'),
    path('students/<int:user_id>/', teacher_student_detail, name='teacher_student_detail'),
]
