from django import forms
from account.models import User
from account.models import Semester

class TeacherEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "department", "accessible_batches"]

    accessible_batches = forms.ModelMultipleChoiceField(
        queryset=Semester.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Accessible Semesters"
    )
