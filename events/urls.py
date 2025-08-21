from django.urls import path
from . import views
from .views import notice_create

urlpatterns = [
    path('', views.notice_list, name='notice_list'),
    path('creat/', notice_create, name='notice_create'),
]
