from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from subject.models import Subject
from student.models import Student
from .models import User,Department
from routine.models import ClassRoutine
from django.contrib import messages
from events.models import Notice
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from attendance.models import AttendanceEntry, Attendance
from django.db.models import Count, Q
from django.db import models
from club.models import Club
from teacher.models import TeacherProfile
from result.models import StudentSGPA
from .models import PasswordResetOTP
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from datetime import datetime, timedelta
import random

OTP_STORE = {}

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
    return render(request, 'login/login.html')


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
    # ensure teacher profile exists
    profile, _ = TeacherProfile.objects.get_or_create(user=teacher)

    # Show subjects in teacher’s department & assigned semesters
    accessible_semesters = teacher.accessible_batches.all()
    subjects = Subject.objects.filter(
        department=teacher.department,
        semester__in=accessible_semesters
    )

    # Today's routines for the teacher
    today_code = datetime.today().strftime("%a").lower()[:3]
    todays_routines = ClassRoutine.objects.filter(
        teacher=teacher,
        day_of_week=today_code
    ).select_related('subject', 'semester').order_by('start_time')

    # Teacher subjects (via routine or M2M)
    teacher_subjects = (
        Subject.objects
        .filter(Q(routines__teacher=teacher) | Q(teachers=teacher))
        .distinct()
        .order_by('name')
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
        "notices": notices,
        "todays_routines": todays_routines,
        "teacher_subjects": teacher_subjects,
        "profile": profile,
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

    # Get user's active clubs
    user_clubs = Club.objects.filter(
        memberships__user=user,
        memberships__status="active"
    )

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

    # Overall SGPA for hero card
    sgpa_qs = StudentSGPA.objects.filter(student=user)
    overall_sgpa = None
    if sgpa_qs.exists():
        vals = [float(x.sgpa) for x in sgpa_qs]
        overall_sgpa = round(sum(vals)/len(vals), 2)

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
        'user_clubs': user_clubs,
        'current_gpa': overall_sgpa,
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


#------------password change -----------------
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


#------------password reset via email with otp -----------------

def send_otp_email(email, otp):
    subject = "Profile Password Reset OTP - Elitte College of Engineering"
    
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f9f9f9; padding:20px;">
        <div style="max-width:600px;margin:auto;background:#fff;padding:20px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.1);">
            <h2 style="color:#2c3e50;text-align:center;">🔑 Password Reset Request</h2>
            <p>Hello,</p>
            <p>We received a request to reset your profile password for your 
            <b>Elitte College of Engineering </b> account.</p>

            <p style="font-size:16px;">Your One-Time Password (OTP) is:</p>
            <h1 style="color:#e74c3c; text-align:center;">{otp}</h1>

            <p>This OTP will expire in <b>10 minutes</b>. Please use it to set a new password.</p>

            <hr style="margin:20px 0;">
            <p style="font-size:14px;color:#555;">📍 Location: Sodpur, North 24 PGS</p>
            <p style="font-size:14px;color:#555;">🙏 Thank you for being part of our family. We pray for your better future!</p>
        </div>
    </body>
    </html>
    """

    msg = EmailMultiAlternatives(subject, f"Your OTP is {otp}. It expires in 10 minutes.", "parveagr@gmail.com", [email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def request_password_reset(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            otp = random.randint(100000, 999999)
            OTP_STORE[email] = {"otp": otp, "expires": timezone.now() + timedelta(minutes=10)}

            send_otp_email(email, otp)
            messages.success(request, "OTP sent to your email. Please check inbox.")
            return redirect("verify_otp")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")
    
    return render(request, "login/request_password_reset.html")


def verify_otp(request):
    if request.method == "POST":
        email = request.POST.get("email")
        otp_entered = request.POST.get("otp")
        new_password = request.POST.get("password")

        if email in OTP_STORE:
            data = OTP_STORE[email]
            if timezone.now() < data["expires"] and str(data["otp"]) == otp_entered:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                del OTP_STORE[email]
                messages.success(request, "Password reset successful! You can now log in.")
                return redirect("login")
            else:
                messages.error(request, "Invalid or expired OTP.")
        else:
            messages.error(request, "No OTP request found for this email.")
    
    return render(request, "login/verify_otp.html")

def custom_logout(request):
    logout(request)
    return redirect('index')