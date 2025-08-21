from django.urls import path
from portal_admin import views

urlpatterns = [
    path("users/", views.user_list_view, name="user_list"),
    path("users/add/", views.user_create_view, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit_view, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete_view, name="user_delete"),
]
