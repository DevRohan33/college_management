from django import forms
from .models import Assignment

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'details', 'subject', 'department', 'semester', 'submit_last_date']
        widgets = {
            'submit_last_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
