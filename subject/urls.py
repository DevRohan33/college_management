from django.urls import path
from . import views

urlpatterns = [
    path('my-subjects/', views.student_subjects, name='student_subjects'),
]
