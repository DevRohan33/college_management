
from django.urls import path
from . import views

urlpatterns = [
    path("new_assignments/", views.create_assignment, name="create_assignment"),
    path("all_assignments/", views.assignment_list, name="assignment_list"),
    path('assignments/<int:pk>/', views.assignment_detail, name='assignment_detail'),
    path("my_assignments/", views.student_assignment_list, name="student_assignment_list"),
    path("submit_assignment/<int:assignment_id>/", views.submit_assignment, name="submit_assignment"),
]

