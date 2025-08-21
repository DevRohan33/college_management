from django.contrib.auth.decorators import user_passes_test, login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import AssignmentForm
from .submitForm import AssignmentSubmissionForm
from .models import Assignment, AssignmentSubmission
from student.models import Student
from django.utils import timezone
from account.models import User

# ----------------- Utility Functions -----------------
def is_teacher(user):
    """Check if user is Teacher or HOD"""
    return hasattr(user, "role") and user.role in ["teacher", "hod"]


# ----------------- Teacher Views -----------------

@login_required
@user_passes_test(is_teacher)
def create_assignment(request):
    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, "Assignment created successfully!")
            return redirect("assignment_list")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = AssignmentForm()
    return render(request, "assignment/create_assignment.html", {"form": form})


@login_required
def assignment_list(request):
    assignments = Assignment.objects.all().order_by("-created_at")
    return render(request, "assignment/assignment_list.html", {"assignments": assignments})

@login_required
@user_passes_test(is_teacher)
def assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)

    # Get all students from the same department + semester as assignment
    all_students = Student.objects.filter(
        user__department=assignment.department,
        user__semester=assignment.semester

    )

    # 🎯 Who submitted
    submitted = AssignmentSubmission.objects.filter(assignment=assignment)
    submitted_students = [sub.student for sub in submitted]

    # 🎯 Who still due
    due_students = all_students.exclude(id__in=[s.id for s in submitted_students])

    # 📊 Stats
    submitted_count = submitted.count()
    due_count = due_students.count()

    context = {
        "assignment": assignment,
        "submitted": submitted,            # list of AssignmentSubmission objects
        "due_students": due_students,      # students who didn’t submit
        "submitted_count": submitted_count,
        "due_count": due_count,
    }
    return render(request, "assignment/assignment_detail.html", context)



# ----------------- Student Views -----------------
@login_required
def student_assignment_list(request):
    if not hasattr(request.user, "student_profile"):
        messages.error(request, "Only students can view this page.")
        return redirect("login")

    student = request.user.student_profile
    assignments = Assignment.objects.filter(
        semester=student.semester, department=student.department
    ).order_by("-created_at")

    # Attach student's submission to each assignment
    for assignment in assignments:
        assignment.submission = assignment.submissions.filter(student=student).first()

    return render(
        request,
        "student_profiles/assignment_list.html",
        {
            "assignments": assignments,
            "student": student,
            "now": timezone.now(),   # ✅ current time
        },
    )

@login_required
def submit_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Student check
    if not hasattr(request.user, "student_profile"):
        messages.error(request, "Only students can submit assignments.")
        return redirect("student_assignment_list")

    student = request.user.student_profile
    user_data = {
        "name": student.user.get_full_name(),
        "reg_no": student.registration_number,
        "mobile_no": student.phone_number,
        "email": student.user.email,
        "department": student.department,
        "semester": student.semester,
    }

    if request.method == "POST":
        form = AssignmentSubmissionForm(
            request.POST, request.FILES, user_data=user_data, assignment=assignment
        )
        if form.is_valid():
            # Prevent duplicate submission
            existing = AssignmentSubmission.objects.filter(
                assignment=assignment, student=student
            ).first()
            if existing:
                messages.warning(request, "You have already submitted this assignment.")
                return redirect("student_assignment_list")

            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = student
            submission.save()
            messages.success(request, "✅ Assignment submitted successfully!")
            return redirect("student_assignment_list")
    else:
        form = AssignmentSubmissionForm(user_data=user_data, assignment=assignment)

    return render(
        request,
        "student_profiles/submit_assignment.html",
        {"form": form, "assignment": assignment, "user_data": user_data},
    )
