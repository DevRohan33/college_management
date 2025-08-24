from django.urls import path
from . import views

urlpatterns = [
    path("classes/", views.classes_routine_view, name="classes_routine"),
    path("classes/create/", views.hod_routine_create, name="hod_routine_create"),
    path("classes/<int:pk>/edit/", views.hod_routine_edit, name="hod_routine_edit"),

    # Teacher
    path("teacher/my-classes/", views.teacher_classes, name="teacher_classes"),
]
