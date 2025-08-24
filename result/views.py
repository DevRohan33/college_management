from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from django.db.models import Q

from .models import ExamSession, ExamMark
from account.models import Semester, Department, User
from subject.models import Subject


@login_required
def teacher_grade_dashboard(request):
    if request.user.role != 'teacher':
        return redirect('index')

    # Show all exam types for semesters the teacher handles
    teacher = request.user

    # subjects assigned (routine or M2M)
    subjects = (
        Subject.objects
        .filter(Q(routines__teacher=teacher) | Q(teachers=teacher))
        .select_related('semester', 'department')
        .distinct()
        .order_by('semester__semester', 'name')
    )

    exam_types = ["CA1", "CA2", "CA3", "CA4"]

    return render(request, 'result/teacher_grade_dashboard.html', {
        'subjects': subjects,
        'exam_types': exam_types,
    })


@login_required
def teacher_grade_entry(request, subject_id, semester_id, exam_type):
    if request.user.role not in ['teacher', 'hod']:
        return redirect('index')

    subject = get_object_or_404(Subject, id=subject_id)
    semester = get_object_or_404(Semester, id=semester_id)

    # Only allow teacher assigned to this subject or HOD of department
    is_assigned_teacher = subject.teachers.filter(id=request.user.id).exists()
    is_hod = request.user.role == 'hod' and request.user.department_id == subject.department_id
    if not (is_assigned_teacher or is_hod):
        messages.error(request, 'You are not allowed to grade this subject.')
        return redirect('teacher_grades')

    # Theory-only CA exams; allow PCA exams as separate types
    if exam_type.startswith('CA') and subject.subject_type != 'theory':
        messages.error(request, 'CA exams apply to theory subjects only.')
        return redirect('teacher_grades')

    # Ensure/create session
    session, created = ExamSession.objects.get_or_create(
        department=subject.department,
        semester=semester,
        subject=subject,
        exam_type=exam_type,
        defaults={
            'created_by': request.user,
            'full_marks': 25,
        }
    )

    # Build/ensure mark rows for students in that semester+department
    students = User.objects.filter(role='student', department=subject.department, semester=semester).order_by('first_name', 'last_name')
    existing = {m.student_id: m for m in ExamMark.objects.filter(session=session)}
    to_create = []
    for stu in students:
        if stu.id not in existing:
            to_create.append(ExamMark(session=session, student=stu))
    if to_create:
        ExamMark.objects.bulk_create(to_create)

    marks_qs = ExamMark.objects.filter(session=session).select_related('student').order_by('student__first_name', 'student__last_name')

    if request.method == 'POST':
        if session.locked:
            messages.error(request, 'This exam session is locked and cannot be modified.')
            return redirect('teacher_grade_entry', subject_id=subject_id, semester_id=semester_id, exam_type=exam_type)

        # Update marks from POST
        updates = []
        for mark in marks_qs:
            val = request.POST.get(f'mark_{mark.student_id}', '')
            if val != '':
                try:
                    num = float(val)
                except ValueError:
                    num = None
                if num is not None:
                    num = max(0, min(num, session.full_marks))
                    mark.marks = num
                    updates.append(mark)
        if updates:
            ExamMark.objects.bulk_update(updates, ['marks'])
            messages.success(request, 'Marks saved successfully.')
        return redirect('teacher_grade_entry', subject_id=subject_id, semester_id=semester_id, exam_type=exam_type)

    return render(request, 'result/teacher_grade_entry.html', {
        'session': session,
        'subject': subject,
        'semester': semester,
        'students': marks_qs,
    })


@login_required
def lock_exam_session(request, session_id):
    session = get_object_or_404(ExamSession, id=session_id)
    # Teachers of the subject or HOD of department can lock
    is_assigned_teacher = session.subject.teachers.filter(id=request.user.id).exists()
    is_hod = request.user.role == 'hod' and request.user.department_id == session.department_id
    if not (is_assigned_teacher or is_hod):
        messages.error(request, 'You are not allowed to lock this exam.')
        return redirect('teacher_grades')

    session.locked = True
    session.locked_at = now()
    session.locked_by = request.user
    session.save(update_fields=['locked', 'locked_at', 'locked_by'])
    messages.success(request, 'Exam session locked. No further edits allowed.')
    return redirect('teacher_grade_entry', subject_id=session.subject_id, semester_id=session.semester_id, exam_type=session.exam_type)


@login_required
def student_result_page(request):
    if request.user.role != 'student':
        return redirect('index')

    user = request.user

    # semester selector: default current semester, allow query param ?sem=<num>
    current_sem_num = user.semester.semester if user.semester else None
    sel_sem_num = request.GET.get('sem')
    try:
        sel_sem_num = int(sel_sem_num) if sel_sem_num else current_sem_num
    except (TypeError, ValueError):
        sel_sem_num = current_sem_num

    # Subject list for selected semester
    subjects = Subject.objects.filter(department=user.department, semester__semester=sel_sem_num).order_by('name') if sel_sem_num else []

    # sessions of selected sem
    sessions = ExamSession.objects.filter(
        department=user.department,
        semester__semester=sel_sem_num
    ).select_related('subject').order_by('subject__name', 'exam_type') if sel_sem_num else []

    # Build CA table rows per subject
    subject_rows = []
    for subj in subjects:
        row = {
            'name': subj.name,
            'code': subj.code,
            'full_marks': 25,
            'CA1': '-', 'CA2': '-', 'CA3': '-', 'CA4': '-',
        }
        for et in ['CA1', 'CA2', 'CA3', 'CA4']:
            s = next((x for x in sessions if x.subject_id == subj.id and x.exam_type == et), None)
            if s:
                m = ExamMark.objects.filter(session=s, student=user).first()
                row[et] = m.marks if m and m.marks is not None else '-'
        subject_rows.append(row)

    # SGPA entries and average
    from .models import StudentSGPA
    sgpa_entries = {r.semester_num: r.sgpa for r in StudentSGPA.objects.filter(student=user)}
    avg_sgpa = None
    if sgpa_entries:
        vals = [float(v) for v in sgpa_entries.values()]
        avg_sgpa = round(sum(vals) / len(vals), 2)

    overall_percent = None
    if avg_sgpa is not None:
        overall_percent = round((avg_sgpa * 10) - 7.5, 2)

    # Build helper lists for template
    sem_range = list(range(1, 9))
    sgpa_rows = [{ 'sem': n, 'sgpa': sgpa_entries.get(n) } for n in sem_range]

    # handle add/update sgpa
    if request.method == 'POST':
        try:
            sem_in = int(request.POST.get('sgpa_sem'))
            sgpa_in = float(request.POST.get('sgpa_val'))
        except (TypeError, ValueError):
            messages.error(request, 'Invalid SGPA input')
            return redirect('student_results_page')
        if not (1 <= sem_in <= 8):
            messages.error(request, 'Semester must be between 1 and 8')
            return redirect('student_results_page')
        from .models import StudentSGPA
        obj, _ = StudentSGPA.objects.update_or_create(
            student=user, semester_num=sem_in,
            defaults={'sgpa': sgpa_in}
        )
        messages.success(request, f'SGPA saved for Sem {sem_in}.')
        return redirect('student_results_page')

    return render(request, 'result/student_results.html', {
        'selected_sem': sel_sem_num,
        'current_sem': current_sem_num,
        'sem_range': sem_range,
        'subject_rows': subject_rows,
        'sgpa_rows': sgpa_rows,
        'avg_sgpa': avg_sgpa,
        'overall_percent': overall_percent,
    })
