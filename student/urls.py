from django.urls import path
from . import views

urlpatterns = [
    path("edit/", views.edit_profile, name="edit_profile"),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
]
