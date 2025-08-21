from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from subject.models import Subject
from student.models import Student

def index(request):
    # If the user is logged in, send them to their dashboard
    if request.user.is_authenticated:
        if hasattr(request.user, 'role'):
            if request.user.role == 'admin':
                return redirect('admin_dashboard')
            elif request.user.role == 'teacher':
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
    # If not logged in, show public index
    return render(request, 'index.html')


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            else:
                return redirect('student_dashboard')
    return render(request, 'login.html')


@login_required
def admin_dashboard(request):
    return render(request, 'dashboards/admin_dashboard.html', {'role': 'Admin'})


@login_required
def teacher_dashboard(request):
    return render(request, 'dashboards/teacher_dashboard.html', {'role': 'Teacher'})


@login_required
def student_dashboard(request):
    user = request.user
    student = getattr(user, "student_profile", None)
    # Fetch subjects based on student's department & semester
    subjects = Subject.objects.filter(
        department=user.department,
        semester=user.semester
    )

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
        'attendance': attendance,
        'notifications': notifications
    })



def custom_logout(request):
    logout(request)
    return redirect('index') 
