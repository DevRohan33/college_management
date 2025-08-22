from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('account.urls')),
    path('', include('student.urls')),
    path('', include('events.urls')),
    path('', include('routine.urls')),
    path("", include("hod.urls")),
    path("", include("portal_admin.urls")),
    path("", include("attendance.urls")),
    path("", include("assignment.urls")),
    path('clubs/', include("club.urls")),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)