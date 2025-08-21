from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from account.models import User
from events.models import Notice 
from datetime import datetime
from routine.models import ClassRoutine
from hod.forms import TeacherEditForm

# Create your views here.
@login_required
def teacher_list_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")

    teachers = User.objects.filter(role="teacher", department=request.user.department)
    return render(request, "hod/teacher_list.html", {"teachers": teachers})

@login_required
def teacher_detail_view(request, pk):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")

    teacher = get_object_or_404(User, pk=pk, role="teacher", department=request.user.department)

    # Today’s day (mon, tue, etc.)
    today = datetime.today().strftime('%a').lower()[:3]

    todays_classes = ClassRoutine.objects.filter(
        teacher=teacher,
        day_of_week=today
    ).order_by("start_time")

    notices = Notice.objects.filter(
        department=request.user.department
    ).order_by("-created_at")[:5]

    return render(request, "hod/teacher_detail.html", {
        "teacher": teacher,
        "todays_classes": todays_classes,
        "notices": notices
    })

@login_required
def teacher_edit(request, pk):
    teacher = get_object_or_404(User, pk=pk, role="teacher")
    if request.method == "POST":
        form = TeacherEditForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            return redirect("teacher_detail", pk=teacher.pk)
    else:
        form = TeacherEditForm(instance=teacher)
    return render(request, "hod/teacher_edit.html", {"form": form, "teacher": teacher})
