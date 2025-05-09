from django import forms
from myapp.models import JobSeeker, Employer, JobPosting, JobApplication, Skill, Benefit, JobAlert, Company, JobCategory
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Company size choices for employer registration
COMPANY_SIZE_CHOICES = [
    ('1-10', '1-10 employees'),
    ('11-50', '11-50 employees'),
    ('51-200', '51-200 employees'),
    ('201-500', '201-500 employees'),
    ('501-1000', '501-1000 employees'),
    ('1000+', '1000+ employees'),
]

COUNTRY_CHOICES = [
    ('', 'Select Country'),
    ('PH', 'Philippines'),
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('CA', 'Canada'),
]

INDUSTRY_CHOICES = [
    ('', 'Select Industry'),
    ('technology', 'Information Technology'),
    ('healthcare', 'Healthcare'),
    ('finance', 'Finance & Banking'),
    ('education', 'Education'),
    ('retail', 'Retail & E-commerce'),
    ('manufacturing', 'Manufacturing'),
    ('construction', 'Construction'),
    ('hospitality', 'Hospitality & Tourism'),
    ('media', 'Media & Entertainment'),
    ('telecom', 'Telecommunications'),
    ('automotive', 'Automotive'),
    ('agriculture', 'Agriculture'),
    ('energy', 'Energy & Utilities'),
    ('real_estate', 'Real Estate'),
    ('logistics', 'Transportation & Logistics'),
    ('consulting', 'Consulting'),
    ('legal', 'Legal Services'),
    ('nonprofit', 'Non-Profit'),
    ('government', 'Government'),
    ('other', 'Other'),
]

class JobSeekerProfileForm(forms.ModelForm):
    class Meta:
        model = JobSeeker
        fields = [
            'phone',
            'location',
            'bio',
            'education',
            'work_experience',
            'skills',
            'expected_salary',
            'preferred_job_types',
            'preferred_locations',
            'profile_picture',
            'resume',
            'professional_summary'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'education': forms.Textarea(attrs={'rows': 4}),
            'work_experience': forms.Textarea(attrs={'rows': 4}),
            'professional_summary': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.TextInput(attrs={'placeholder': 'Enter skills separated by commas'}),
            'preferred_locations': forms.TextInput(attrs={'placeholder': 'Enter preferred locations separated by commas'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['profile_picture', 'resume']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = Employer
        fields = ['company', 'job_title', 'department', 'phone', 'is_primary_contact', 'can_post_jobs']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'is_primary_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_post_jobs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class JobPostingForm(forms.ModelForm):
    required_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True
    )
    
    preferred_skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )
    
    benefits = forms.ModelMultipleChoiceField(
        queryset=Benefit.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )

    category = forms.ModelChoiceField(
        queryset=JobCategory.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        empty_label="Select a Category"
    )

    class Meta:
        model = JobPosting
        fields = [
            'title', 'description', 'requirements', 'job_type',
            'location', 'salary_min', 'salary_max', 'is_active',
            'application_deadline', 'experience_level', 'required_skills',
            'preferred_skills', 'benefits', 'category'
        ]
        widgets = {
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, employer=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employer = employer
        self.fields['required_skills'].widget.attrs['class'] = 'select2-multiple'
        self.fields['preferred_skills'].widget.attrs['class'] = 'select2-multiple'
        self.fields['benefits'].widget.attrs['class'] = 'select2-multiple'
        
        # Make certain fields optional
        self.fields['salary_min'].required = False
        self.fields['salary_max'].required = False
        self.fields['application_deadline'].required = False
        self.fields['preferred_skills'].required = False
        self.fields['benefits'].required = False

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        application_deadline = cleaned_data.get('application_deadline')

        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError('Minimum salary cannot be greater than maximum salary')

        if application_deadline and application_deadline < timezone.now():
            raise ValidationError('Application deadline cannot be in the past')

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.employer:
            instance.company = self.employer.company
        if commit:
            instance.save()
            self.save_m2m()
        return instance

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ApplicationUpdateForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'resume']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make resume field optional when updating
        self.fields['resume'].required = False
        # Add help text for resume field
        self.fields['resume'].help_text = 'Leave empty to keep the current resume'

class EmployerRegistrationForm(UserCreationForm):
    company_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    industry = forms.ChoiceField(
        choices=INDUSTRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    company_size = forms.ChoiceField(
        choices=COMPANY_SIZE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    company_description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    location = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    job_title = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'company_name', 
                 'industry', 'company_size', 'website', 'company_description',
                 'location', 'country', 'job_title', 'department', 'phone')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_staff = True  # Set is_staff to True for employers
        
        if commit:
            user.save()
            
            # Create or get the company first
            company = Company.objects.create(
                name=self.cleaned_data['company_name'],
                industry=self.cleaned_data['industry'],
                description=self.cleaned_data['company_description'],
                website=self.cleaned_data['website'],
                location=self.cleaned_data['location']
            )
            
            # Create the employer profile
            if not hasattr(user, 'myapp_employer'):
                employer = Employer.objects.create(
                    user=user,
                    company=company,
                    country=self.cleaned_data['country'],
                    job_title=self.cleaned_data['job_title'],
                    department=self.cleaned_data.get('department', ''),
                    phone=self.cleaned_data['phone'],
                    is_primary_contact=True,  # Make them primary contact by default
                    can_post_jobs=True  # Allow them to post jobs by default
                )
            
        return user

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

class JobAlertForm(forms.ModelForm):
    class Meta:
        model = JobAlert
        fields = [
            'keywords', 'job_type', 'category', 'location', 
            'min_salary', 'frequency', 'is_active'
        ]
        widgets = {
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Job title keywords'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., New York, NY'}),
            'min_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minimum salary'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ApplicationStatusUpdateForm(forms.ModelForm):
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text='Optional comments about the status change'
    )

    class Meta:
        model = JobApplication
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True, changed_by=None):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Create history entry if status has changed
            if instance.status != instance._original_status:
                from myapp.models import ApplicationStatusHistory
                ApplicationStatusHistory.objects.create(
                    application=instance,
                    status=instance.status,
                    notes=self.cleaned_data.get('comments', ''),
                    created_by=changed_by
                )
        return instance
