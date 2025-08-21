from django.contrib.auth.decorators import login_required
from .models import ClassRoutine
from account.models import User
from django.shortcuts import render, redirect, get_object_or_404
from .form import RoutineForm 
# ----------------- Student Routine -----------------
@login_required
def student_routine_view(request):
    if request.user.role != "student":
        return redirect("index")

    student = student.objects.get(user=request.user)
    routines = ClassRoutine.objects.filter(
        department=student.department,
        semester=student.semester
    ).order_by("day_of_week", "start_time")

    return render(request, "routine/student_routine.html", {"routines": routines})

# ----------------- HOD Routine -----------------
@login_required
def hod_routine_view(request):
    if request.user.role != "hod":
        return redirect("index")

    routines = ClassRoutine.objects.filter(
        department=request.user.department
    ).order_by("semester", "day_of_week", "start_time")

    return render(request, "routine/hod_routine.html", {"routines": routines})

# ----------------- Classes Routine (HOD) -----------------
@login_required
def classes_routine_view(request):
    if request.user.role != "hod":
        return redirect("index")

    from account.models import Semester
    semesters = Semester.objects.all().order_by("semester")

    selected_semester = request.GET.get("semester")

    routines = ClassRoutine.objects.filter(department=request.user.department)

    if selected_semester:
        routines = routines.filter(semester_id=selected_semester)

    routines = routines.order_by("day_of_week", "semester__semester", "start_time")

    return render(request, "hod/classes_routine.html", {
        "routines": routines,
        "semesters": semesters,
        "selected_semester": selected_semester,
    })


@login_required
def hod_routine_create(request):
    if request.user.role != "hod":
        return redirect("index")

    if request.method == "POST":
        form = RoutineForm(request.POST)
        if form.is_valid():
            routine = form.save(commit=False)
            # Automatically set department of logged-in HOD
            routine.department = request.user.department
            routine.save()
            return redirect("classes_routine")  # redirect to classes dashboard
    else:
        form = RoutineForm()

    return render(request, "hod/hod_routine_create.html", {"form": form})

@login_required
def hod_routine_edit(request, pk):
    if request.user.role != "hod":
        return redirect("index")

    routine = get_object_or_404(ClassRoutine, pk=pk, department=request.user.department)

    if request.method == "POST":
        form = RoutineForm(request.POST, instance=routine)
        if form.is_valid():
            form.save()
            return redirect("classes_routine")
    else:
        form = RoutineForm(instance=routine)

    return render(request, "hod/hod_routine_edit.html", {"form": form, "routine": routine})

# ----------------- Teacher Routine -----------------
@login_required
def teacher_routine_view(request):
    if request.user.role != "teacher":
        return redirect("index")

    routines = ClassRoutine.objects.filter(
        teacher=request.user
    ).order_by("day_of_week", "start_time")

    return render(request, "routine/teacher_routine.html", {"routines": routines})
