from django.shortcuts import render
from .models import Subject

def student_subjects(request):
    # Example: fetch subjects for the logged-in student
    user = request.user
    
    subjects = Subject.objects.filter(
        department=user.department,
        semester=user.semester
    )

    return render(request, 'student_dashboard.html', {
        'subjects': subjects
    })
