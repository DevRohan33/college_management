from django import forms
from .models import Student

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "profile_image",
            "phone_number",
            "session",
            "aap_id",
            "registration_number",
            "roll_no",
            "address",
        ]
