from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import User
from .models import JobSeeker, Employer, Company, Skill, JobPosting, JobApplication, JobCategory, JobAlert, SavedSearch, Notification, AnalyticsReport
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import Form
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from allauth.account.forms import LoginForm

COUNTRY_CHOICES = [
    ('PH', 'Philippines'),
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('CA', 'Canada'),
]

class BaseSignupForm(forms.Form):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, required=True)
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        initial='PH',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-placeholder': 'Select your country'
        })
    )
    user_type = forms.ChoiceField(
        choices=[
            ('jobseeker', 'Job Seeker'),
            ('employer', 'Employer')
        ],
        required=True,
        widget=forms.RadioSelect
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['user_type', 'country']:
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['user_type'].widget.attrs.update({'class': 'form-check-input'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if get_user_model().objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, request=None):
        User = get_user_model()
        user = User.objects.create_user(
            username=self.cleaned_data['email'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )

        user_type = self.cleaned_data['user_type']
        if user_type == 'jobseeker':
            JobSeeker.objects.create(
                user=user,
                country=self.cleaned_data['country']
            )
        elif user_type == 'employer':
            Employer.objects.create(
                user=user,
                country=self.cleaned_data['country']
            )

        return user

class CustomLoginForm(LoginForm):
    login = forms.CharField(
        label=_("Username or Email"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username or email'
        })
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

class CustomResetPasswordForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

class CustomResetPasswordKeyForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class CustomChangePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

class JobSeekerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )
    
    # Override password fields to add proper styling and validation
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'new-password'
        }),
        help_text=None
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        }),
        help_text=None
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., +1 (555) 123-4567'})
    )
    location = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York, NY'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your address'})
    )
    professional_summary = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Brief summary of your professional background'})
    )
    education = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Your educational background'})
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Your work experience'})
    )
    skills = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Your skills (e.g., Python, JavaScript, Project Management)'})
    )
    expected_salary = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected annual salary'})
    )
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
    ]
    preferred_job_types = forms.MultipleChoiceField(
        choices=JOB_TYPE_CHOICES,
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )
    preferred_locations = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Preferred work locations'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'location', 
                 'address', 'professional_summary', 'education', 'experience', 
                 'skills', 'expected_salary', 'preferred_job_types', 'preferred_locations')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        
        # Remove the default help text and use our custom help text in the template
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None
        
        # Add password validation attributes
        self.fields['password1'].widget.attrs.update({
            'minlength': '8',
            'pattern': '(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}',
            'title': 'Password must contain at least 8 characters, including uppercase, lowercase, and numbers'
        })
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2
        
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in password1):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in password1):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in password1):
            raise forms.ValidationError("Password must contain at least one number.")
        return password1

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            
            # Create or update the job seeker profile
            if not hasattr(user, 'myapp_jobseeker'):
                job_seeker = JobSeeker.objects.create(
                user=user,
                    phone=self.cleaned_data['phone'],
                    location=self.cleaned_data['location'],
                    address=self.cleaned_data['address'],
                    professional_summary=self.cleaned_data['professional_summary'],
                    education=self.cleaned_data['education'],
                    work_experience=self.cleaned_data['experience'],
                    expected_salary=self.cleaned_data['expected_salary'],
                    preferred_locations=self.cleaned_data['preferred_locations'],
                    # Store preferred job types as comma-separated string
                    preferred_job_types=','.join(self.cleaned_data['preferred_job_types'])
                )
                
                # Handle skills separately after creation
                if self.cleaned_data['skills']:
                    skill_names = [s.strip() for s in self.cleaned_data['skills'].split(',')]
                    skills = []
                    for skill_name in skill_names:
                        skill, created = Skill.objects.get_or_create(name=skill_name.lower())
                        skills.append(skill)
                    job_seeker.skills.set(skills)
            else:
                # Update existing job seeker profile
                job_seeker = user.myapp_jobseeker
                job_seeker.phone = self.cleaned_data['phone']
                job_seeker.location = self.cleaned_data['location']
                job_seeker.address = self.cleaned_data['address']
                job_seeker.professional_summary = self.cleaned_data['professional_summary']
                job_seeker.education = self.cleaned_data['education']
                job_seeker.work_experience = self.cleaned_data['experience']
                job_seeker.expected_salary = self.cleaned_data['expected_salary']
                job_seeker.preferred_locations = self.cleaned_data['preferred_locations']
                # Store preferred job types as comma-separated string
                job_seeker.preferred_job_types = ','.join(self.cleaned_data['preferred_job_types'])
                
                # Handle skills update
                if self.cleaned_data['skills']:
                    skill_names = [s.strip() for s in self.cleaned_data['skills'].split(',')]
                    skills = []
                    for skill_name in skill_names:
                        skill, created = Skill.objects.get_or_create(name=skill_name.lower())
                        skills.append(skill)
                    job_seeker.skills.set(skills)
                else:
                    job_seeker.skills.clear()
                    
                job_seeker.save()
                
        return user

class EmployerRegistrationForm(UserCreationForm):
    company_name = forms.CharField(max_length=100, required=True)
    industry = forms.CharField(max_length=100, required=True)
    company_size = forms.IntegerField(required=True)
    website = forms.URLField(required=False)
    company_description = forms.CharField(widget=forms.Textarea, required=False)
    location = forms.CharField(max_length=100, required=True)
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        initial='PH',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-placeholder': 'Select your country'
        })
    )
    job_title = forms.CharField(max_length=100, required=True)
    department = forms.CharField(max_length=100, required=False)

    class Meta:
        model = get_user_model()
        fields = ('username', 'email', 'password1', 'password2', 'company_name',
                 'industry', 'company_size', 'website', 'company_description',
                 'location', 'country', 'job_title', 'department')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_employer = True
        if commit:
            user.save()
            company = Company.objects.create(
                name=self.cleaned_data['company_name'],
                industry=self.cleaned_data['industry'],
                employee_count=self.cleaned_data['company_size'],
                website=self.cleaned_data.get('website', ''),
                description=self.cleaned_data.get('company_description', ''),
                location=self.cleaned_data['location']
            )
            employer = Employer.objects.create(
                user=user,
                company=company,
                country=self.cleaned_data['country'],
                job_title=self.cleaned_data['job_title'],
                department=self.cleaned_data.get('department', '')
            )
        return user

class JobPostingForm(forms.ModelForm):
    class Meta:
        model = JobPosting
        fields = [
            'title', 'description', 'requirements', 'company', 'category',
            'job_type', 'experience_level', 'location', 'application_deadline',
            'salary_min', 'salary_max', 'required_skills', 'preferred_skills',
            'benefits', 'cost_per_day', 'is_active', 'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'requirements': forms.Textarea(attrs={'rows': 4}),
            'application_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'required_skills': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'preferred_skills': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'benefits': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'cost_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the company field to the current user's company
        if 'initial' not in kwargs and hasattr(self, 'request') and hasattr(self.request.user, 'myapp_employer'):
            self.fields['company'].initial = self.request.user.myapp_employer.company
            self.fields['company'].widget = forms.HiddenInput()

    def clean_application_deadline(self):
        deadline = self.cleaned_data['application_deadline']
        if deadline <= timezone.now():
            raise forms.ValidationError("Application deadline must be in the future.")
        return deadline

    def clean_salary(self):
        salary_min = self.cleaned_data.get('salary_min')
        salary_max = self.cleaned_data.get('salary_max')
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError("Minimum salary cannot be greater than maximum salary.")
        return salary_min, salary_max

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobSeeker
        fields = ['bio', 'location', 'country', 'skills', 'experience_level', 'expected_salary', 'phone', 'education', 'professional_summary', 'preferred_locations', 'profile_picture']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].required = False

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeeker  # Ensure this model is imported and exists
        fields = ['bio', 'location', 'country', 'skills', 'experience_level', 'expected_salary', 'phone', 'education', 'professional_summary', 'preferred_locations', 'profile_picture']

class ContactForm(forms.Form):
    employer = forms.ModelChoiceField(queryset=Employer.objects.select_related('user').all(), required=True, label='Contact Employer', widget=forms.Select(attrs={'class': 'form-control'}))
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=200, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = Employer
        fields = [
            'job_title', 'department', 'phone', 'country',
            'credentials', 'resume', 'notify_new_applications', 'notify_messages'
        ]
        widgets = {
            'credentials': forms.Textarea(attrs={'rows': 4}),
        }
