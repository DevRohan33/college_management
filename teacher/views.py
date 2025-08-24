from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TeacherProfile
from .forms import TeacherProfileForm
from account.models import User, Semester
from attendance.models import AttendanceEntry


@login_required
def teacher_profile_view(request):
    if request.user.role != 'teacher':
        return redirect('index')

    profile, _ = TeacherProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = TeacherProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('teacher_profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherProfileForm(instance=profile)

    return render(request, 'teacher/profile.html', {
        'profile': profile,
        'form': form,
    })


@login_required
def teacher_students_list(request):
    if request.user.role != 'teacher':
        return redirect('index')

    dept = request.user.department
    semesters = Semester.objects.filter(department=dept).order_by('semester')

    semester_id = request.GET.get('semester')
    students = User.objects.filter(role='student', department=dept)
    if semester_id and semester_id != 'all':
        students = students.filter(semester_id=semester_id)

    students = students.select_related('semester').order_by('first_name', 'last_name')

    return render(request, 'teacher/students_list.html', {
        'semesters': semesters,
        'students': students,
        'selected_semester': semester_id or 'all',
    })


@login_required
def teacher_student_detail(request, user_id):
    if request.user.role != 'teacher':
        return redirect('index')

    student = get_object_or_404(User, id=user_id, role='student', department=request.user.department)

    # Attendance records for this student
    entries = (
        AttendanceEntry.objects
        .filter(student=student)
        .select_related('attendance__subject', 'attendance__semester')
        .order_by('-attendance__date')
    )

    # Dummy results for now
    results = [
        { 'subject': 'Data Structures', 'grade': 'A', 'marks': 88 },
        { 'subject': 'Algorithms', 'grade': 'B+', 'marks': 81 },
        { 'subject': 'DBMS', 'grade': 'A-', 'marks': 85 },
    ]

    return render(request, 'teacher/student_detail.html', {
        'student': student,
        'entries': entries,
        'results': results,
    })
