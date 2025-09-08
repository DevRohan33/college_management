from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages # Important for displaying messages
from account.models import User
from events.models import Notice 
from datetime import datetime
from routine.models import ClassRoutine
from hod.forms import TeacherEditForm, HODProfileForm 
from hod.models import HOD  # Assuming you have an HOD model

# HOD Dashboard View
@login_required
def hod_dashboard_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # Get or create HOD profile for the current user
    # This line is the fix for the RelatedObjectDoesNotExist error
    hod_profile, created = HOD.objects.get_or_create(user=request.user)

    # Example data for dashboard (you can expand this)
    total_teachers = User.objects.filter(role="teacher", department=request.user.department).count()
    recent_notices = Notice.objects.filter(
        department=request.user.department
    ).order_by("-created_at")[:3] # Get 3 most recent notices

    context = {
        'total_teachers': total_teachers,
        'recent_notices': recent_notices,
        'hod_profile': hod_profile, # Use the retrieved or created hod_profile
    }
    return render(request, "hod/dashboard.html", context)


# Teacher Management Views
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

    # Today's day (mon, tue, etc.)
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
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
        
    teacher = get_object_or_404(User, pk=pk, role="teacher", department=request.user.department)
    
    if request.method == "POST":
        form = TeacherEditForm(request.POST, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher profile updated successfully!')
            return redirect("teacher_detail", pk=teacher.pk)
    else:
        form = TeacherEditForm(instance=teacher)
    return render(request, "hod/teacher_edit.html", {"form": form, "teacher": teacher})


# HOD Profile Management Views
@login_required
def hod_edit_profile(request):
    # Check if user is HOD
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # Get or create HOD profile for the current user
    hod_profile, created = HOD.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = HODProfileForm(request.POST, request.FILES, instance=hod_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('hod_edit_profile')
    else:
        form = HODProfileForm(instance=hod_profile)
    
    context = {
        'form': form,
        'hod': hod_profile,
        'user': request.user
    }
    return render(request, 'hod/hod_edit_profile.html', context)

@login_required
def hod_change_password(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # You'll need to create a password change form and handle it here.
    # This is a placeholder for now.
    messages.info(request, "Password change functionality not yet implemented.")
    return render(request, 'hod/hod_change_password.html')


# Other HOD-related Views
@login_required
def classes_routine_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # Logic to fetch and display class routines for the HOD's department
    # For example:
    # department_routines = ClassRoutine.objects.filter(subject__department=request.user.department).order_by('day_of_week', 'start_time')
    
    context = {
        'message': 'This is the Classes Routine page for HODs.',
        # 'department_routines': department_routines,
    }
    return render(request, "hod/classes_routine.html", context)

@login_required
def hod_subjects_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # Logic to fetch and display subjects for the HOD's department
    # For example:
    # subjects = Subject.objects.filter(department=request.user.department)
    
    context = {
        'message': 'This is the Subjects Management page for HODs.',
        # 'subjects': subjects,
    }
    return render(request, "hod/subjects.html", context)

@login_required
def notice_list_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # Logic to list all notices relevant to the HOD's department
    notices = Notice.objects.filter(department=request.user.department).order_by('-created_at')
    
    context = {
        'notices': notices,
    }
    return render(request, "hod/notice_list.html", context)

@login_required
def notice_create_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # You'll need a form for creating notices (e.g., NoticeForm)
    # This is a placeholder.
    if request.method == 'POST':
        # form = NoticeForm(request.POST)
        # if form.is_valid():
        #     notice = form.save(commit=False)
        #     notice.author = request.user
        #     notice.department = request.user.department # Assuming notices are department-specific
        #     notice.save()
        messages.success(request, "Notice posted successfully! (Placeholder functionality)")
        return redirect('notice_list')
    else:
        # form = NoticeForm()
        pass

    context = {
        'message': 'Create a new Notice (Placeholder form).',
        # 'form': form,
    }
    return render(request, "hod/notice_create.html", context)




@login_required
def classes_routine_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    selected_semester_id = request.GET.get('semester')
    routines = ClassRoutine.objects.filter(subject__department=request.user.department)

    if selected_semester_id:
        routines = routines.filter(semester__id=selected_semester_id)

    routines = routines.order_by('day_of_week', 'start_time')
    semesters = semesters.objects.all().order_by('semester') # Fetch all semesters for the filter

    context = {
        'routines': routines,
        'semesters': semesters,
        'selected_semester': selected_semester_id,
    }
    return render(request, "hod/classes_routine.html", context)


@login_required
def hod_subjects_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # You'll need to import your Subject model from the correct app, e.g., from subject.models import Subject
    # For now, using a placeholder if Subject model is not provided in context
    # subjects = Subject.objects.filter(department=request.user.department)
    subjects = [] # Placeholder: Replace with actual query
    
    context = {
        'message': 'This is the Subjects Management page for HODs.',
        'subjects': subjects, # Pass actual subjects here
    }
    return render(request, "hod/subjects.html", context) # Assuming you have hod/subjects.html template


@login_required
def notice_list_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    notices = Notice.objects.filter(department=request.user.department).order_by('-created_at')
    
    context = {
        'notices': notices,
    }
    return render(request, "hod/notice_list.html", context)

@login_required
def notice_create_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    # You'll need a form for creating notices (e.g., NoticeForm from events.forms)
    # from events.forms import NoticeForm # Uncomment and import if you have it
    
    if request.method == 'POST':
        # form = NoticeForm(request.POST) # Use your actual NoticeForm
        # if form.is_valid():
        #     notice = form.save(commit=False)
        #     notice.author = request.user
        #     notice.department = request.user.department
        #     notice.save()
        messages.success(request, "Notice posted successfully! (Placeholder functionality)")
        return redirect('notice_list')
    else:
        # form = NoticeForm() # Use your actual NoticeForm
        pass

    context = {
        'message': 'Create a new Notice (Placeholder form).',
        # 'form': form,
    }
    return render(request, "hod/notice_create.html", context)


@login_required
def hod_routine_create_view(request):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    form = ClassRoutineForm() # Use the form defined above or your actual form
    if request.method == 'POST':
        form = ClassRoutineForm(request.POST)
        if form.is_valid():
            routine = form.save(commit=False)
            routine.save()
            messages.success(request, "Class routine created successfully!")
            return redirect('classes_routine')
    
    context = {'form': form}
    return render(request, 'hod/hod_routine_create.html', context)


@login_required
def hod_routine_edit_view(request, pk):
    if getattr(request.user, "role", "").lower() != "hod":
        return redirect("index")
    
    routine = get_object_or_404(ClassRoutine, pk=pk, subject__department=request.user.department)
    form = ClassRoutineForm(instance=routine) # Use the form defined above or your actual form
    if request.method == 'POST':
        form = ClassRoutineForm(request.POST, instance=routine)
        if form.is_valid():
            form.save()
            messages.success(request, "Class routine updated successfully!")
            return redirect('classes_routine')
    
    context = {'form': form}
    return render(request, 'hod/hod_routine_edit.html', context)

