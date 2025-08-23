from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('account.urls')),
    path('student', include('student.urls')),
    path('event', include('events.urls')),
    path('routine', include('routine.urls')),
    path('hod', include("hod.urls")),
    path('portal_admin', include("portal_admin.urls")),
    path('attendence', include("attendance.urls")),
    path('assignment', include("assignment.urls")),
    path('clubs/', include("club.urls")),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)