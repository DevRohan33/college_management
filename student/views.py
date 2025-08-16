from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import StudentProfileForm
from .models import Student
from subject.models import Subject
from routine.models import ClassRoutine

@login_required
def edit_profile(request):
    student, created = Student.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = StudentProfileForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            return redirect("edit_profile") 
    else:
        form = StudentProfileForm(instance=student)

    return render(request, "student_profiles/edit_profile.html", {
        "form": form,
        "student": student,
    })


@login_required
def student_dashboard(request):
    user = request.user
    student = getattr(user, "student_profile", None)

    # Fetch subjects based on student's department & semester
    subjects = Subject.objects.filter(
        department=user.department,
        semester=user.semester
    )

    # Fetch class routine for student's department & semester
    routines = ClassRoutine.objects.filter(
        department=user.department,
        semester=user.semester
    ).order_by('day_of_week', 'start_time')

    # Example dummy attendance & notifications
    attendance = {
        'total': 50,
        'attended': 45,
        'percentage': round((45 / 50) * 100, 2)
    }
    notifications = [
        "Mid-term exams start next Monday.",
        "Project submission deadline extended."
    ]

    return render(request, 'dashboards/student_dashboard.html', {
        'role': 'Student',
        'student': student,
        'subjects': subjects,
        'routines': routines,
        'attendance': attendance,
        'notifications': notifications
    })
