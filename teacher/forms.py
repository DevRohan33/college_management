from django import forms
from .models import TeacherProfile


class TeacherProfileForm(forms.ModelForm):
    ability_subjects = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., Data Structures, Algorithms, DBMS'}),
        help_text='Comma-separated subjects you can teach'
    )

    class Meta:
        model = TeacherProfile
        fields = [
            'profile_image', 'phone_number', 'address',
            'degree', 'primary_subject', 'ability_subjects', 'bio'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
