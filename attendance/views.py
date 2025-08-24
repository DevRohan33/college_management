from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import now
from django.db.models import Count, Q

from .models import Attendance, AttendanceEntry
from account.models import Semester
from subject.models import Subject
from routine.models import ClassRoutine

# Helpers
DAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

def _today_code():
    return DAY_CODES[now().date().weekday()]

def _teacher_pairs(teacher):
    # Unique (subject_id, semester_id) pairs from:
    #  - routine assignments for this teacher
    #  - subjects directly assigned to this teacher (M2M)
    routine_pairs = (
        ClassRoutine.objects
        .filter(teacher=teacher)
        .values_list("subject_id", "semester_id")
        .distinct()
    )
    m2m_pairs = (
        Subject.objects
        .filter(teachers=teacher)
        .values_list("id", "semester_id")
        .distinct()
    )
    return set(routine_pairs) | set(m2m_pairs)


def _attendance_taken_keys(department, date, pairs):
    # Return set of keys "{subject_id}-{semester_id}" for which attendance exists on date
    qs = Attendance.objects.filter(department=department, date=date)
    if pairs:
        # limit to teacher's pairs
        disj = Q()
        for sid, semid in pairs:
            disj |= Q(subject_id=sid, semester_id=semid)
        if disj:
            qs = qs.filter(disj)
    return {f"{a.subject_id}-{a.semester_id}" for a in qs.only("subject_id", "semester_id")}


# Create your views here.
@login_required
def take_attendance(request):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    # Teacher's subjects: include both routine assignments and directly assigned via M2M
    from django.db.models import Q
    subjects = (
        Subject.objects
        .filter(Q(routines__teacher=request.user) | Q(teachers=request.user))
        .distinct()
        .order_by('name')
    )

    # Teacher's routine classes
    routines = ClassRoutine.objects.filter(teacher=request.user).order_by("day_of_week", "start_time")

    today_code = _today_code()
    pairs = _teacher_pairs(request.user)
    taken_keys = _attendance_taken_keys(request.user.department, now().date(), pairs)

    return render(request, "teacher/take_attendance.html", {
        "subjects": subjects,
        "routines": routines,
        "today_code": today_code,
        "taken_keys": taken_keys,  # set of "subject-semester" strings
    })


@login_required
def mark_attendance(request, subject_id, semester_id):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    subject = get_object_or_404(Subject, id=subject_id)
    semester = get_object_or_404(Semester, id=semester_id)

    # verify that this teacher is assigned this subject+semester in routine AND today is the class day
    today_code = _today_code()
    is_today_class = ClassRoutine.objects.filter(
        teacher=request.user,
        subject=subject,
        semester=semester,
        day_of_week=today_code,
    ).exists()

    if not is_today_class:
        messages.error(request, "You can only take attendance on the scheduled class day. Use 'Custom Attendance' for extra sessions.")
        return redirect("take_attendance")

    # get all students of this semester and teacher's department
    students = request.user.department.user_set.filter(role="student", semester=semester)

    # Ensure single attendance per date
    attendance, created = Attendance.objects.get_or_create(
        subject=subject,
        semester=semester,
        department=request.user.department,
        date=now().date(),
    )

    if request.method == "POST":
        # overwrite entries if submitted again -> treated as edit
        attendance.entries.all().delete()

        bulk_entries = []
        for student in students:
            status = request.POST.get(f"status_{student.id}", "absent")
            bulk_entries.append(AttendanceEntry(
                attendance=attendance,
                student=student,
                status=status
            ))
        AttendanceEntry.objects.bulk_create(bulk_entries)
        messages.success(request, "Attendance saved successfully.")
        return redirect("take_attendance")

    return render(request, "teacher/mark_attendance.html", {
        "subject": subject,
        "semester": semester,
        "students": students,
        "attendance": attendance,
    })


@login_required
def mark_attendance_custom(request):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    subject_id = request.GET.get("subject")
    semester_id = request.GET.get("semester")

    if not subject_id:
        messages.error(request, "Please select a subject.")
        return redirect("take_attendance")

    subject = get_object_or_404(Subject, id=subject_id)

    # If semester not provided, fallback to the subject's semester
    if semester_id:
        semester = get_object_or_404(Semester, id=semester_id)
        # Guard: selected semester must match subject's semester
        if getattr(subject, 'semester_id', None) and subject.semester_id != semester.id:
            messages.error(request, "Selected subject is not assigned to the chosen semester.")
            return redirect("take_attendance")
    else:
        semester = subject.semester

    # all students in that semester + teacher’s department
    students = request.user.department.user_set.filter(role="student", semester=semester)

    # get/create attendance for today (department auto-filled from teacher)
    attendance, created = Attendance.objects.get_or_create(
        subject=subject,
        semester=semester,
        department=request.user.department,
        date=now().date(),
    )

    if request.method == "POST":
        # overwrite previous entries to allow edits on resubmission
        attendance.entries.all().delete()

        bulk_entries = []
        for student in students:
            status = request.POST.get(f"status_{student.id}", "absent")
            bulk_entries.append(AttendanceEntry(
                attendance=attendance,
                student=student,
                status=status
            ))
        AttendanceEntry.objects.bulk_create(bulk_entries)
        messages.success(request, "Attendance saved successfully.")
        return redirect("take_attendance")

    return render(request, "teacher/mark_attendance.html", {
        "subject": subject,
        "semester": semester,
        "students": students,
        "attendance": attendance,
    })


#--------------- Teacher: Attendance History & Export ----------------
@login_required
def teacher_attendance_history(request):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    pairs = _teacher_pairs(request.user)
    rows = []
    for sid, semid in sorted(pairs, key=lambda x: (x[1], x[0])):
        subject = Subject.objects.get(id=sid)
        semester = Semester.objects.get(id=semid)
        sessions = Attendance.objects.filter(
            department=request.user.department,
            subject_id=sid,
            semester_id=semid,
        ).order_by("-date")
        rows.append({
            "subject": subject,
            "semester": semester,
            "count": sessions.count(),
            "last_date": sessions.first().date if sessions.exists() else None,
        })

    return render(request, "teacher/attendance_history.html", {
        "rows": rows,
    })


@login_required
def teacher_subject_attendance_history(request, subject_id, semester_id):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    # ensure teacher owns this pair
    if (subject_id, semester_id) not in _teacher_pairs(request.user):
        messages.error(request, "You are not assigned to this subject/semester.")
        return redirect("teacher_attendance_history")

    subject = get_object_or_404(Subject, id=subject_id)
    semester = get_object_or_404(Semester, id=semester_id)

    sessions = (
        Attendance.objects
        .filter(
            department=request.user.department,
            subject_id=subject_id,
            semester_id=semester_id,
        )
        .annotate(
            present_count=Count('entries', filter=Q(entries__status__iexact='present')),
            absent_count=Count('entries', filter=Q(entries__status__iexact='absent')),
            total_count=Count('entries')
        )
        .order_by("-date")
    )

    return render(request, "teacher/attendance_subject_history.html", {
        "subject": subject,
        "semester": semester,
        "sessions": sessions,
    })


@login_required
def teacher_attendance_detail(request, attendance_id):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    attendance = get_object_or_404(Attendance, id=attendance_id, department=request.user.department)
    # Permission: teacher must be assigned to this subject/semester
    if (attendance.subject_id, attendance.semester_id) not in _teacher_pairs(request.user):
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_attendance_history")

    entries = attendance.entries.select_related("student").all().order_by("student__first_name", "student__last_name")

    present = entries.filter(status__iexact="present").count()
    absent = entries.filter(status__iexact="absent").count()

    return render(request, "teacher/attendance_detail.html", {
        "attendance": attendance,
        "entries": entries,
        "present": present,
        "absent": absent,
    })


@login_required
def export_class_attendance(request, attendance_id):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    attendance = get_object_or_404(Attendance, id=attendance_id, department=request.user.department)
    if (attendance.subject_id, attendance.semester_id) not in _teacher_pairs(request.user):
        messages.error(request, "You are not assigned to this class.")
        return redirect("teacher_attendance_history")

    entries = attendance.entries.select_related("student").all().order_by("student__first_name", "student__last_name")

    # Export as Excel-compatible HTML table (no extra deps)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    filename = f"attendance_{attendance.subject.name}_sem{attendance.semester.semester}_{attendance.date}.xls".replace(" ", "_")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    html = [
        "<html><head><meta charset='utf-8'></head><body>",
        f"<h3>Attendance - {attendance.subject.name} (Semester {attendance.semester.semester}) - {attendance.date}</h3>",
        "<table border='1' cellpadding='5' cellspacing='0'>",
        "<tr><th>#</th><th>Student Name</th><th>Registration</th><th>Status</th><th>Marked At</th></tr>",
    ]
    for i, e in enumerate(entries, start=1):
        html.append(
            f"<tr><td>{i}</td><td>{e.student.get_full_name()}</td><td>{getattr(e.student, 'registration_number', '')}</td><td>{e.status.title()}</td><td>{e.marked_at}</td></tr>"
        )
    html.append("</table></body></html>")

    response.write("".join(html))
    return response


@login_required
def export_attendance_report(request):
    if getattr(request.user, "role", None) != "teacher":
        return redirect("index")

    period = request.GET.get("period", "weekly")  # weekly | monthly | custom
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    download = request.GET.get("download") == "1"

    today = now().date()
    if period == "weekly":
        start_date, end_date = (today - __import__("datetime").timedelta(days=7)), today
    elif period == "monthly":
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = parse_date(start_str) if start_str else None
        end_date = parse_date(end_str) if end_str else None
        if not start_date or not end_date:
            # fall back to last 30 days
            start_date, end_date = (today - __import__("datetime").timedelta(days=30)), today

    pairs = _teacher_pairs(request.user)
    disj = Q()
    for sid, semid in pairs:
        disj |= Q(subject_id=sid, semester_id=semid)

    sessions = Attendance.objects.filter(
        department=request.user.department,
        date__range=(start_date, end_date),
    )
    if disj:
        sessions = sessions.filter(disj)
    sessions = sessions.order_by("date", "subject__name")

    if not download:
        # Render filter UI
        return render(request, "teacher/export_attendance.html", {
            "period": period,
            "start": start_date,
            "end": end_date,
            "session_count": sessions.count(),
        })

    # Build entries and totals
    total_present = 0
    total_absent = 0

    # Excel-compatible HTML
    response = HttpResponse(content_type='application/vnd.ms-excel')
    filename = f"attendance_report_{start_date}_to_{end_date}.xls"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    parts = [
        "<html><head><meta charset='utf-8'></head><body>",
        f"<h3>Attendance Report ({start_date} to {end_date})</h3>",
        "<table border='1' cellpadding='5' cellspacing='0'>",
        "<tr><th>Date</th><th>Subject</th><th>Semester</th><th>Present</th><th>Absent</th><th>Total</th></tr>",
    ]

    for s in sessions:
        present = s.entries.filter(status__iexact="present").count()
        absent = s.entries.filter(status__iexact="absent").count()
        total_present += present
        total_absent += absent
        parts.append(
            f"<tr><td>{s.date}</td><td>{s.subject.name}</td><td>{s.semester.semester}</td><td>{present}</td><td>{absent}</td><td>{present+absent}</td></tr>"
        )

    parts.append("</table>")
    parts.append(f"<p><strong>Total Present:</strong> {total_present} &nbsp;&nbsp; <strong>Total Absent:</strong> {total_absent}</p>")
    parts.append("</body></html>")

    response.write("".join(parts))
    return response


#---------------student views----------------
@login_required
def student_attendance(request):
    if getattr(request.user, "role", None) != "student":
        return redirect("index")

    start = request.GET.get("start")
    end = request.GET.get("end")

    entries = AttendanceEntry.objects.filter(student=request.user)

    # Date filter
    if start:
        start_date = parse_date(start)
        if start_date:
            entries = entries.filter(attendance__date__gte=start_date)
    if end:
        end_date = parse_date(end)
        if end_date:
            entries = entries.filter(attendance__date__lte=end_date)

    # Counts
    total_present = entries.filter(status__iexact="present").count()
    total_absent = entries.filter(status__iexact="absent").count()
    total_classes = total_present + total_absent

    overall_percent = round((total_present / total_classes) * 100, 2) if total_classes else 0

    # Subject stats
    subject_stats = {}
    for e in entries:
        sid = e.attendance.subject_id
        sname = e.attendance.subject.name
        if sid not in subject_stats:
            subject_stats[sid] = {
                "subject_id": sid,
                "subject": sname,
                "present": 0,
                "absent": 0,
            }

        if e.status.lower() == "present":
            subject_stats[sid]["present"] += 1
        else:
            subject_stats[sid]["absent"] += 1

    # Percent per subject
    for rec in subject_stats.values():
        total = rec["present"] + rec["absent"]
        rec["total"] = total
        rec["percent"] = round((rec["present"] / total) * 100, 2) if total else 0.0

    subject_stats_list = sorted(subject_stats.values(), key=lambda x: x["subject"].lower())

    # Chart data
    chart_labels = [s["subject"] for s in subject_stats_list]
    chart_percents = [s["percent"] for s in subject_stats_list]
    chart_present = [s["present"] for s in subject_stats_list]
    chart_absent = [s["absent"] for s in subject_stats_list]
    chart_total = [s["total"] for s in subject_stats_list]

    # Daily timeline %
    timeline = {}
    for e in entries:
        d = e.attendance.date.isoformat()
        timeline.setdefault(d, {"present": 0, "total": 0})
        timeline[d]["total"] += 1
        if e.status.lower() == "present":
            timeline[d]["present"] += 1

    timeline_labels = sorted(timeline.keys())
    timeline_percent = [
        round((day["present"] / day["total"]) * 100, 2) if day["total"] else 0
        for day in (timeline[d] for d in timeline_labels)
    ]

    context = {
        "student": request.user,
        "start": start or "",
        "end": end or "",
        "entries": entries[:200],
        "total_present": total_present,
        "total_absent": total_absent,
        "total_classes": total_classes,
        "overall_percent": overall_percent,
        "subject_stats": subject_stats_list,
        "chart_labels": chart_labels,
        "chart_percents": chart_percents,
        "chart_present": chart_present,
        "chart_absent": chart_absent,
        "chart_total": chart_total,
        "timeline_labels": timeline_labels,
        "timeline_percent": timeline_percent,
        "benchmark": 75,
        "today": now().date(),
    }
    return render(request, "student_profiles/attendance.html", context)
