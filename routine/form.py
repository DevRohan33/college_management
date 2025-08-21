from django import forms
from .models import ClassRoutine

class RoutineForm(forms.ModelForm):
    class Meta:
        model = ClassRoutine
        fields = [
            "department",
            "semester",
            "day_of_week",
            "start_time",
            "end_time",
            "subject",
            "teacher",
        ]
        widgets = {
            "day_of_week": forms.Select(attrs={"class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }
