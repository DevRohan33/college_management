from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from account.models import User
from portal_admin.forms import UserForm


# ✅ Check if user is superuser or admin
def is_admin(user):
    return user.is_superuser or user.role == "management"


# ✅ List all users
@login_required
@user_passes_test(is_admin)
def user_list_view(request):
    users = User.objects.all().order_by("-date_joined")  # Latest first
    return render(request, "admin/user_list.html", {"users": users})


# ✅ Add new user
@login_required
@user_passes_test(is_admin)
def user_create_view(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' added successfully!")
            return redirect(reverse_lazy("user_list"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserForm()

    return render(request, "admin/user_form.html", {"form": form, "title": "Add User"})


# ✅ Edit user
@login_required
@user_passes_test(is_admin)
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user.username}' updated successfully!")
            return redirect(reverse_lazy("user_list"))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserForm(instance=user)

    return render(request, "admin/user_form.html", {"form": form, "title": "Edit User"})


# ✅ Delete user
@login_required
@user_passes_test(is_admin)
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        messages.success(request, f"User '{user.username}' deleted successfully!")
        user.delete()
        return redirect(reverse_lazy("user_list"))

    return render(request, "admin/user_confirm_delete.html", {"user": user})
