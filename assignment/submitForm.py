from django import forms
from .models import AssignmentSubmission

class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['file']  # Only upload allowed

    def __init__(self, *args, **kwargs):
        user_data = kwargs.pop('user_data', None)
        assignment = kwargs.pop('assignment', None)
        super().__init__(*args, **kwargs)

        # Read-only info (not saved in DB, only for display)
        if user_data and assignment:
            self.fields['name'] = forms.CharField(initial=user_data['name'], disabled=True)
            self.fields['reg_no'] = forms.CharField(initial=user_data['reg_no'], disabled=True)
            self.fields['mobile_no'] = forms.CharField(initial=user_data['mobile_no'], disabled=True)
            self.fields['email'] = forms.EmailField(initial=user_data['email'], disabled=True)
            self.fields['department'] = forms.CharField(initial=user_data['department'], disabled=True)
            self.fields['semester'] = forms.CharField(initial=user_data['semester'], disabled=True)
            self.fields['subject'] = forms.CharField(initial=assignment.subject, disabled=True)
            self.fields['topic'] = forms.CharField(initial=assignment.title, disabled=True)
