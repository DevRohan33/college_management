from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, Semester
from django import forms


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")

        # Management - no dept/semester
        if role == "management":
            cleaned_data["department"] = None
            cleaned_data["semester"] = None

        # HOD - must select department, semester cleared
        elif role == "hod":
            if not cleaned_data.get("department"):
                raise forms.ValidationError("HOD must be assigned to a department.")
            cleaned_data["semester"] = None

        # Teacher - must select department, semester cleared
        elif role == "teacher":
            if not cleaned_data.get("department"):
                raise forms.ValidationError("Teacher must be assigned to a department.")
            cleaned_data["semester"] = None

        # Student - department + semester
        elif role == "student":
            if not cleaned_data.get("department") or not cleaned_data.get("semester"):
                raise forms.ValidationError("Student must be assigned department and semester.")

        return cleaned_data
    
# Customizing the User Admin
class CustomUserAdmin(UserAdmin):
    form = UserAdminForm
    model = User
    list_display = ('username', 'email', 'get_full_name', 'role', 'department', 'semester')
    list_filter = ('role', 'department', 'semester')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'

    # Restrict dept for HODs
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if request.user.role == "hod":
            form.base_fields["department"].queryset = Department.objects.filter(
                id=request.user.department_id
            )
        return form

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        role_fields = ("role", "department", "semester")

        if obj:
            if obj.role == "management":
                role_fields = ("role",)
            elif obj.role in ["hod", "teacher"]:
                role_fields = ("role", "department")
            elif obj.role == "student":
                role_fields = ("role", "department", "semester")

        new_fieldsets = []
        for title, fields in fieldsets:
            if title == "Role & Department":
                new_fieldsets.append(("Role & Department", {"fields": role_fields}))
            else:
                new_fieldsets.append((title, fields))
        return new_fieldsets

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'first_name', 'last_name', 'email', 'role', 'department', 'semester', 'password1', 'password2'),
        }),
    )

# Register
admin.site.register(User, CustomUserAdmin)
admin.site.register(Department)
admin.site.register(Semester)
