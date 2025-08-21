from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Attendance, AttendanceEntry
from account.models import Semester
from subject.models import Subject
from django.db.models import Count, Q
from django.utils.dateparse import parse_date
from django.utils.timezone import now

from .models import AttendanceEntry

# Create your views here.
@login_required
def take_attendance(request):
    if request.user.role != "teacher":
        return redirect("index")

    from subject.models import Subject
    from routine.models import ClassRoutine  # assuming you have this model

    # Teacher's subjects
    subjects = Subject.objects.filter(semester__department=request.user.department)

    # Teacher's routine classes (today’s or all)
    routines = ClassRoutine.objects.filter(teacher=request.user).order_by("day_of_week", "start_time")

    return render(request, "teacher/take_attendance.html", {
        "subjects": subjects,
        "routines": routines,
    })

@login_required
def mark_attendance(request, subject_id, semester_id):
    if request.user.role != "teacher":
        return redirect("index")

    subject = get_object_or_404(Subject, id=subject_id)
    semester = get_object_or_404(Semester, id=semester_id)

    # get all students of this semester
    students = request.user.department.user_set.filter(role="student", semester=semester)

    # check if today's attendance already exists
    attendance, created = Attendance.objects.get_or_create(
        subject=subject,
        semester=semester,
        department=request.user.department,
        date=now().date()
    )

    if request.method == "POST":
        # delete old entries if re-submitted
        attendance.entries.all().delete()

        for student in students:
            status = request.POST.get(f"status_{student.id}", "absent")
            AttendanceEntry.objects.create(
                attendance=attendance,
                student=student,
                status=status
            )
        return redirect("take_attendance")

    return render(request, "teacher/mark_attendance.html", {
        "subject": subject,
        "semester": semester,
        "students": students,
        "attendance": attendance,
    })


@login_required
def mark_attendance_custom(request):
    if request.user.role != "teacher":
        return redirect("index")

    subject_id = request.GET.get("subject")
    if not subject_id:
        return redirect("take_attendance")

    subject = get_object_or_404(Subject, id=subject_id)
    semester = subject.semester

    # all students in that semester + teacher’s department
    students = request.user.department.user_set.filter(role="student", semester=semester)

    # get/create attendance for today
    attendance, created = Attendance.objects.get_or_create(
        subject=subject,
        semester=semester,
        department=request.user.department,
        date=now().date()
    )

    if request.method == "POST":
        attendance.entries.all().delete()

        for student in students:
            status = request.POST.get(f"status_{student.id}", "absent")
            AttendanceEntry.objects.create(
                attendance=attendance,
                student=student,
                status=status
            )
        return redirect("take_attendance")

    return render(request, "teacher/mark_attendance.html", {
        "subject": subject,
        "semester": semester,
        "students": students,
        "attendance": attendance,
    })

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
        "chart_absent": chart_absent,   # ✅ add absent dataset
        "chart_total": chart_total,
        "timeline_labels": timeline_labels,
        "timeline_percent": timeline_percent,
        "benchmark": 75,
        "today": now().date(),
    }
    return render(request, "student_profiles/attendance.html", context)
