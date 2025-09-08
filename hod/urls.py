from django.urls import path
from . import views

urlpatterns = [

    path("teachers/", views.teacher_list_view, name="teacher_list"),
    path("teachers/<int:pk>/", views.teacher_detail_view, name="teacher_detail"),
    path("teachers/<int:pk>/edit/", views.teacher_edit, name="teacher_edit"),
    path('hod/profile/edit/', views.hod_edit_profile, name='hod_edit_profile'),
    path('hod/change-password/', views.hod_change_password, name='hod_change_password'),
    # Uncomment the hod_dashboard path
    path("hod-dashboard/", views.hod_dashboard_view, name="hod_dashboard"), # Changed to hod_dashboard_view for consistency with your views.py
    path("hod/subjects/", views.hod_subjects_view, name="hod_subjects"), # Uncommented this line
    path("hod/routine/create/", views.hod_routine_create_view, name="hod_routine_create"), # Assuming you'll create this view
    path("hod/routine/<int:pk>/edit/", views.hod_routine_edit_view, name="hod_routine_edit"), # Assuming you'll create this view
    path("notices/", views.notice_list_view, name="notice_list"),
    path("notices/create/", views.notice_create_view, name="notice_create"),
]