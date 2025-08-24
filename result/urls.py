from django.urls import path
from .views import teacher_grade_dashboard, teacher_grade_entry, lock_exam_session, student_result_page

urlpatterns = [
    path('teacher/grades/', teacher_grade_dashboard, name='teacher_grades'),
    path('teacher/grades/entry/<int:subject_id>/<int:semester_id>/<str:exam_type>/', teacher_grade_entry, name='teacher_grade_entry'),
    path('teacher/grades/lock/<int:session_id>/', lock_exam_session, name='lock_exam_session'),
    path('student/results/', student_result_page, name='student_results_page'),
]
