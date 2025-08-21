
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import StudentProfileForm
from .models import Student


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


    # If your file is elsewhere, please adjust this path.
    return render(request, "student_profiles/edit_profile.html", {
        "form": form,
        "student": student,
    })
