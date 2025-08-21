from django.urls import path
from . import views

urlpatterns = [

    path("teachers/", views.teacher_list_view, name="teacher_list"),
    path("teachers/<int:pk>/", views.teacher_detail_view, name="teacher_detail"),
    path("teachers/<int:pk>/edit/", views.teacher_edit, name="teacher_edit"),

]
