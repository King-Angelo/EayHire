from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile

class SecureUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'user_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Password must be at least 8 characters long'

class StudentProfileForm(forms.ModelForm):
    privacy_consent = forms.BooleanField(required=True)
    
    class Meta:
        model = StudentProfile
        fields = ('resume', 'phone')

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            validate_file_size(resume)
            validate_file_type(resume)
        return resume 