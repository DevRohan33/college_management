from django.shortcuts import render
from .models import ClassRoutine
from account.models import Student

def student_routine_view(request):
    student = Student.objects.get(user=request.user)  # get student profile
    routines = ClassRoutine.objects.filter(
        department=student.department,
        semester=student.semester
    ).order_by('day_of_week', 'start_time')  # sort nicely

    return render(request, 'student_routine.html', {'routines': routines})
