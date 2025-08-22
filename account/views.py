from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from subject.models import Subject
from student.models import Student
from .models import User,Department
from routine.models import ClassRoutine
from django.contrib import messages
from events.models import Notice
from datetime import datetime
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from attendance.models import AttendanceEntry, Attendance
from django.db.models import Count
from django.db import models

# ------------------ VIEWS ------------------
def index(request):
    # If the user is logged in, send them to their dashboard
    if request.user.is_authenticated:
        role = getattr(request.user, "role", "").lower() 
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'management':
            return redirect('management_dashboard')
        elif role == 'hod':
            return redirect('hod_dashboard')
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
            role = getattr(user, "role", "").lower()
            if role == 'admin':
                return redirect('admin_dashboard')
            elif role == 'teacher':
                return redirect('teacher_dashboard')
            elif role == 'management':
                return redirect('management_dashboard')
            elif role == 'hod':
                return redirect('hod_dashboard')
            else:
                return redirect('student_dashboard')
    return render(request, 'login.html')


# ------------------ DASHBOARDS ------------------

@login_required
def admin_dashboard(request):
    if getattr(request.user, "role", "").lower() != 'admin':
        return redirect('index')
    
    total_users = User.objects.count()
    total_students = User.objects.filter(role="student").count()
    total_teachers = User.objects.filter(role="teacher").count()
    total_departments = Department.objects.count()

    students = User.objects.filter(role="student")
    teachers = User.objects.filter(role="teacher")
    departments = Department.objects.all()

    context = {
        "role": "Admin",
        "total_users": total_users,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_departments": total_departments,
        "students": students,
        "teachers": teachers,
        "departments": departments,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
def management_dashboard(request):
    if getattr(request.user, "role", "").lower() != "management":
        return redirect("index")

    # Broad overview across departments
    departments = Department.objects.all()
    stats = []
    for dept in departments:
        stats.append({
            "department": dept.name,
            "students": User.objects.filter(role="student", department=dept).count(),
            "teachers": User.objects.filter(role="teacher", department=dept).count(),
        })

    context = {
        "role": "Management",
        "department_stats": stats,
        "total_departments": departments.count(),
        "total_students": User.objects.filter(role="student").count(),
        "total_teachers": User.objects.filter(role="teacher").count(),
    }
    return render(request, "dashboards/management_dashboard.html", context)


@login_required
def hod_dashboard(request):
    if request.user.role != "hod":
        return redirect("index")

    dept = request.user.department

    teachers = User.objects.filter(role="teacher", department=dept)
    students = User.objects.filter(role="student", department=dept)
    subjects = Subject.objects.filter(department=dept)
    routines = ClassRoutine.objects.filter(department=dept)
    notices = Notice.objects.filter(department=dept).order_by("-created_at")

    context = {
        "role": "Head of Department",
        "department": dept,
        "teachers": teachers,
        "students": students,
        "subjects": subjects,
        "routines": routines,
        "total_teachers": teachers.count(),
        "total_students": students.count(),
        "notices": notices,
    }
    return render(request, "dashboards/hod_dashboard.html", context)


@login_required
def teacher_dashboard(request):
    if request.user.role != "teacher":
        return redirect("index")

    teacher = request.user

    # Show subjects in teacher’s department & assigned semesters
    accessible_semesters = teacher.accessible_batches.all()
    subjects = Subject.objects.filter(
        department=teacher.department,
        semester__in=accessible_semesters
    )

    student_count = User.objects.filter(
        role="student",
        department=teacher.department,
        semester__in=accessible_semesters
    ).count()

    notices = Notice.objects.filter(department=teacher.department).order_by('-created_at')

    context = {
        "role": "Teacher",
        "subjects": subjects,
        "total_classes": subjects.count(),
        "total_students": student_count,
        "notices": notices
    }
    return render(request, "dashboards/teacher_dashboard.html", context)



@login_required
def student_dashboard(request):
    user = request.user
    student = getattr(user, "student_profile", None)

    # Fetch subjects based on student's department & semester
    subjects = Subject.objects.filter(
        department=user.department,
        semester=user.semester
    )

    today = datetime.today().strftime("%a").lower()[:3]  # mon, tue, wed...

    # Today's schedule
    todays_routines = ClassRoutine.objects.filter(
        department=user.department,
        semester=user.semester,
        day_of_week=today
    ).order_by("start_time")

    # Weekly schedule
    weekly_routines = ClassRoutine.objects.filter(
        department=user.department,
        semester=user.semester
    ).order_by("day_of_week", "start_time")

    # ttendance summary
    entries = AttendanceEntry.objects.filter(student=user)
    total_present = entries.filter(status__iexact="present").count()
    total_absent = entries.filter(status__iexact="absent").count()
    total_classes = total_present + total_absent
    overall_percent = round((total_present / total_classes) * 100, 2) if total_classes else 0
    notifications = [
        "Mid-term exams start next Monday.",
        "Project submission deadline extended."
    ]

    subject_stats = (
        entries.values("attendance__subject__name")
        .annotate(
            present=Count("id", filter=models.Q(status__iexact="present")),
            absent=Count("id", filter=models.Q(status__iexact="absent")),
        )
        .order_by("attendance__subject__name")
    )
    for s in subject_stats:
        total = s["present"] + s["absent"]
        s["total"] = total
        s["percent"] = round((s["present"] / total) * 100, 2) if total else 0

    notices = Notice.objects.filter(
        department=user.department
    ).order_by('-created_at')

    return render(request, 'dashboards/student_dashboard.html', {
        'role': 'Student',
        'student': student,
        'subjects': subjects,
        'todays_routines': todays_routines,
        'weekly_routines': weekly_routines,
        "attendance_total": total_classes,
        "attendance_present": total_present,
        "attendance_absent": total_absent,
        "attendance_percent": overall_percent,
        "attendance_subject_stats": subject_stats,
        'notifications': notifications,
        'notices': notices,
    })

# --- NEW, SEPARATE FUNCTION FOR THE RESULTS PAGE ---
@login_required
def student_results(request):
    context = {
        'results': []
    }
    return render(request, 'student/student_results.html', context)

@login_required
def student_courses(request):
    user = request.user
    subjects = Subject.objects.filter(
        department=user.department,
        semester=user.semester
    )
    return render(request, 'student_profiles/courses.html', {'subjects': subjects})

@login_required
def event_list(request):
    notices = Notice.objects.all().order_by('-created_at')
    return render(request, 'event/notice_list.html', {'notices': notices})

@login_required
def student_change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been updated successfully.")
            return redirect("student_dashboard")
        else:
            print(form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "student_profiles/password_change.html", {"form": form})

def custom_logout(request):
    logout(request)
    return redirect('index')