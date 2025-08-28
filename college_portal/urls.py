from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings
from django.conf import settings
import os

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('account.urls')),
    path('student', include('student.urls')),
    path('event', include('events.urls')),
    path('routine', include('routine.urls')),
    path('teacher', include('teacher.urls')),
    path('hod', include("hod.urls")),
    path('portal_admin', include("portal_admin.urls")),
    path('attendence', include("attendance.urls")),
    path('assignment', include("assignment.urls")),
    path('clubs/', include("club.urls")),
    path('result', include('result.urls')),
    path('shop/', include('shop.urls')),
    path("", include("chatbot.urls")),
]

