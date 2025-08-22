from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
     path('management-dashboard/', views.management_dashboard, name='management_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path("change-password/", views.student_change_password, name="student_change_password"),
    path('hod-dashboard/', views.hod_dashboard, name='hod_dashboard'),
    path('my-results/', views.student_results, name='student_results'),
    path('courses/', views.student_courses, name='student_courses'),
    path('events/', views.event_list, name='event_list'),
]
