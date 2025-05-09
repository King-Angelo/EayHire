import django_filters
from django.db.models import Q
from myapp.models import JobPosting, JobCategory, Skill, Employer, Company, JobSeeker, JobApplication
from django_filters import rest_framework as filters

class JobPostingFilter(filters.FilterSet):
    title = filters.CharFilter(lookup_expr='icontains')
    company = filters.CharFilter(field_name='company__name', lookup_expr='icontains')
    location = filters.CharFilter(field_name='location', lookup_expr='icontains')
    job_type = filters.ChoiceFilter(choices=JobPosting.JOB_TYPE_CHOICES)
    experience_level = filters.ChoiceFilter(choices=JobPosting.EXPERIENCE_LEVEL_CHOICES)
    category = filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    required_skills = filters.CharFilter(field_name='required_skills__name', lookup_expr='icontains')
    preferred_skills = filters.CharFilter(field_name='preferred_skills__name', lookup_expr='icontains')
    salary_min = filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    is_active = filters.BooleanFilter()
    is_featured = filters.BooleanFilter()
    application_deadline = filters.DateFilter(field_name='application_deadline', lookup_expr='gte')
    experience_required = filters.NumberFilter(field_name='experience_required', lookup_expr='lte')
    is_remote = filters.BooleanFilter(field_name='is_remote')

    class Meta:
        model = JobPosting
        fields = [
            'title', 'company', 'location', 'job_type', 'experience_level',
            'category', 'required_skills', 'preferred_skills', 'salary_min',
            'salary_max', 'is_active', 'is_featured', 'application_deadline',
            'experience_required', 'is_remote'
        ]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        
        # Add search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(company__name__icontains=search) |
                Q(location__icontains=search)
            ).distinct()
        
        return queryset

class EmployerFilter(filters.FilterSet):
    username = filters.CharFilter(field_name='user__username', lookup_expr='icontains')
    email = filters.CharFilter(field_name='user__email', lookup_expr='icontains')
    company_name = filters.CharFilter(field_name='company__name', lookup_expr='icontains')
    position = filters.CharFilter(lookup_expr='icontains')
    is_verified = filters.BooleanFilter()
    industry = filters.CharFilter(field_name='company__industry', lookup_expr='icontains')
    location = filters.CharFilter(field_name='company__location', lookup_expr='icontains')

    class Meta:
        model = Employer
        fields = [
            'username', 'email', 'company_name', 'position',
            'is_verified', 'industry', 'location'
        ]

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        
        # Add search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__email__icontains=search) |
                Q(company__name__icontains=search) |
                Q(position__icontains=search) |
                Q(company__industry__icontains=search) |
                Q(company__location__icontains=search)
            ).distinct()
        
        return queryset

class JobSeekerFilter(filters.FilterSet):
    experience_min = filters.NumberFilter(field_name='experience_years', lookup_expr='gte')
    experience_max = filters.NumberFilter(field_name='experience_years', lookup_expr='lte')
    skills = filters.CharFilter(field_name='skills__name', lookup_expr='icontains')
    location = filters.CharFilter(field_name='location', lookup_expr='icontains')

    class Meta:
        model = JobSeeker
        fields = ['experience_min', 'experience_max', 'skills', 'location']

class JobApplicationFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=JobApplication.STATUS_CHOICES)
    applied_after = filters.DateFilter(field_name='applied_at', lookup_expr='gte')
    applied_before = filters.DateFilter(field_name='applied_at', lookup_expr='lte')
    
    class Meta:
        model = JobApplication
        fields = ['status', 'applied_after', 'applied_before'] 