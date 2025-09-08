# from django import forms
# from account.models import User
# from account.models import Semester

# class TeacherEditForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ["username", "email", "department", "accessible_batches"]

#     accessible_batches = forms.ModelMultipleChoiceField(
#         queryset=Semester.objects.all(),
#         widget=forms.CheckboxSelectMultiple,
#         required=False,
#         label="Accessible Semesters"
#     )


from django import forms
from account.models import User, Semester # Assuming Semester is still in account.models
from .models import HOD # Import your HOD model from the current app

class TeacherEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "department", "accessible_batches"]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}), # Assuming department is a ForeignKey or ChoiceField
            # accessible_batches widget is defined below
        }

    accessible_batches = forms.ModelMultipleChoiceField(
        queryset=Semester.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}), # Added class for styling
        required=False,
        label="Accessible Semesters"
    )

    # Optional: If you want to customize how department is displayed for teachers (e.g., read-only)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['department'].widget.attrs['disabled'] = 'disabled' # Make department read-only if desired
        # self.fields['department'].required = False # If read-only, it shouldn't be required


class HODProfileForm(forms.ModelForm):
    class Meta:
        model = HOD
        fields = [
            "profile_image",
            "phone_number",
            "employee_id",
            "qualification",
            "experience_years",
            "joining_date",
            "specialization",
            "office_address",
            "bio",
        ]
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), # HTML5 date picker
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'office_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            # profile_image usually handled with default FileInput or custom widget if needed
        }

    # Include User model fields that HOD can also edit for themselves
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate initial values for User fields from the instance's associated User object
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['profile_image', 'accessible_batches'] and 'class' not in field.widget.attrs:
                if isinstance(field.widget, (forms.TextInput, forms.EmailInput, forms.NumberInput, forms.Textarea, forms.DateInput, forms.Select)):
                    field.widget.attrs['class'] = 'form-control'
                elif isinstance(field.widget, forms.CheckboxInput):
                    field.widget.attrs['class'] = 'form-check-input'

    def save(self, commit=True):
        # Save HOD instance
        hod = super().save(commit=False)
        
        # Update and save the associated User instance
        user = hod.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            hod.save()
        return hod