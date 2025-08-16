from django.contrib import admin
from .models import Attendance, AttendanceEntry
# Register your models here.

admin.site.register(Attendance)
admin.site.register(AttendanceEntry)