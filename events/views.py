from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notice
from .forms import NoticeForm

# Create your views here.
def notice_list(request):
    notices = Notice.objects.all().order_by('-created_at')
    return render(request, 'event/notice_list.html', {'notices': notices})

@login_required
def notice_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        # Automatically assign department and creator
        department = getattr(request.user, 'department', None)
        notice = Notice.objects.create(
            title=title,
            description=description,
            created_by=request.user,
            department=department.name if department else ''
        )
        return redirect('teacher_dashboard')  # redirect after creation

    return render(request, 'event/notice_create.html')