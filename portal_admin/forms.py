# forms.py
from django import forms
from account.models import User, Department, Semester
from django.contrib.auth.hashers import make_password


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
        required=False,  # for edit case
        help_text="Leave blank if you don’t want to change the password."
    )

    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "username", "email",
            "password", "role", "department", "semester"
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Style improvements (Bootstrap/Tailwind friendly)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

        # Department & Semester filtering
        self.fields["department"].queryset = Department.objects.all()
        self.fields["semester"].queryset = Semester.objects.none()

        if "department" in self.data:
            try:
                department_id = int(self.data.get("department"))
                self.fields["semester"].queryset = Semester.objects.filter(department_id=department_id).order_by("name")
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.department:
            self.fields["semester"].queryset = self.instance.department.semesters.all().order_by("name")

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if self.instance.pk:  # Editing user
            if not password:
                return self.instance.password  # Keep old password
        return make_password(password)  # Hash new password
