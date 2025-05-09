from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count, F, Q
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

COUNTRY_CHOICES = [
    ('PH', 'Philippines'),
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('CA', 'Canada'),
]

class JobCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Job Categories"

    def __str__(self):
        return self.name

class Skill(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, related_name='skills')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Benefit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class JobPosting(models.Model):
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('temporary', 'Temporary'),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive Level'),
    ]

    title = models.CharField(max_length=200)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='job_postings')
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    requirements = models.TextField()
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES)
    location = models.CharField(max_length=200)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    required_skills = models.ManyToManyField(Skill, related_name='required_for_jobs')
    preferred_skills = models.ManyToManyField(Skill, related_name='preferred_for_jobs', blank=True)
    benefits = models.ManyToManyField(Benefit, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    application_deadline = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    applications_count = models.PositiveIntegerField(default=0)
    cost_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    time_to_fill = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('job_detail', args=[str(self.id)])

    @property
    def is_expired(self):
        return timezone.now() > self.application_deadline

    def update_metrics(self):
        self.views_count = self.view_logs.count()
        self.applications_count = self.applications.count()
        self.save()

    def calculate_match_score(self, job_seeker):
        # Calculate skill match
        required_skills = set(self.required_skills.values_list('id', flat=True))
        preferred_skills = set(self.preferred_skills.values_list('id', flat=True))
        seeker_skills = set(job_seeker.skills.values_list('id', flat=True))
        
        required_match = len(required_skills & seeker_skills) / len(required_skills) if required_skills else 1
        preferred_match = len(preferred_skills & seeker_skills) / len(preferred_skills) if preferred_skills else 1
        
        skill_score = (required_match * 0.7 + preferred_match * 0.3) * 100
        
        # Calculate experience match
        experience_levels = {'entry': 1, 'mid': 2, 'senior': 3, 'executive': 4}
        job_level = experience_levels.get(self.experience_level, 0)
        seeker_level = experience_levels.get(job_seeker.experience_level, 0)
        
        experience_score = max(0, (1 - abs(job_level - seeker_level) / 3)) * 100
        
        # Calculate salary match
        if self.salary_min and self.salary_max and job_seeker.expected_salary:
            salary_min = float(self.salary_min)
            salary_max = float(self.salary_max)
            expected_salary = float(job_seeker.expected_salary)
            if expected_salary < salary_min:
                salary_score = max(0, (expected_salary / salary_min) * 100)
            elif expected_salary > salary_max:
                salary_score = max(0, (salary_max / expected_salary) * 100)
            else:
                salary_score = 100
        else:
            salary_score = 50  # Default score if salary info is missing
        
        # Calculate location match
        from geopy.distance import geodesic
        if job_seeker.latitude and job_seeker.longitude:
            distance = geodesic(
                (job_seeker.latitude, job_seeker.longitude),
                (self.latitude, self.longitude)
            ).miles
            location_score = max(0, (100 - distance) / 100) * 100
        else:
            location_score = 50  # Default score if location info is missing
        
        # Calculate final score
        final_score = (
            skill_score * 0.4 +
            experience_score * 0.3 +
            salary_score * 0.2 +
            location_score * 0.1
        )
        
        return {
            'total_score': final_score,
            'skill_match': skill_score,
            'experience_match': experience_score,
            'salary_match': salary_score,
            'location_match': location_score
        }

class JobMetrics(models.Model):
    job = models.OneToOneField(JobPosting, on_delete=models.CASCADE, related_name='metrics')
    views = models.PositiveIntegerField(default=0)  # Total views
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    total_applications = models.PositiveIntegerField(default=0)
    shortlisted_applications = models.PositiveIntegerField(default=0)
    interviewed_applications = models.PositiveIntegerField(default=0)
    offered_applications = models.PositiveIntegerField(default=0)
    accepted_applications = models.PositiveIntegerField(default=0)
    average_match_score = models.FloatField(null=True, blank=True)
    time_to_first_application = models.DurationField(null=True, blank=True)
    time_to_shortlist = models.DurationField(null=True, blank=True)
    time_to_hire = models.DurationField(null=True, blank=True)
    cost_per_application = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_per_hire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Metrics for {self.job.title}"

    class Meta:
        verbose_name_plural = "Job Metrics"
        indexes = [
            models.Index(fields=['job']),
            models.Index(fields=['last_updated']),
        ]

    def update_metrics(self):
        # Update view counts
        self.views = self.job.view_logs.count()
        self.total_views = self.views
        self.unique_views = self.job.view_logs.values('user').distinct().count()

        # Update application counts
        applications = self.job.applications.all()
        self.total_applications = applications.count()
        self.shortlisted_applications = applications.filter(status='shortlisted').count()
        self.interviewed_applications = applications.filter(status='interviewing').count()
        self.offered_applications = applications.filter(status='offered').count()
        self.accepted_applications = applications.filter(status='accepted').count()

        # Calculate average match score
        match_scores = applications.exclude(match_score__isnull=True).values_list('match_score', flat=True)
        if match_scores:
            self.average_match_score = sum(match_scores) / len(match_scores)
        else:
            self.average_match_score = None

        # Calculate time metrics
        if applications.exists():
            first_application = applications.order_by('applied_at').first()
            if first_application and self.job.created_at:
                self.time_to_first_application = first_application.applied_at - self.job.created_at

            shortlisted = applications.filter(status='shortlisted').order_by('updated_at').first()
            if shortlisted and self.job.created_at:
                self.time_to_shortlist = shortlisted.updated_at - self.job.created_at

            hired = applications.filter(status='accepted').order_by('updated_at').first()
            if hired and self.job.created_at:
                self.time_to_hire = hired.updated_at - self.job.created_at

        # Calculate cost metrics
        if self.total_applications > 0 and self.job.cost_per_day is not None:
            total_cost = self.job.cost_per_day * (timezone.now() - self.job.created_at).days
            self.cost_per_application = total_cost / self.total_applications
            if self.accepted_applications > 0:
                self.cost_per_hire = total_cost / self.accepted_applications
            else:
                self.cost_per_hire = None
        else:
            self.cost_per_application = None
            self.cost_per_hire = None

        self.save()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('application_received', 'Application Received'),
        ('application_status_changed', 'Application Status Changed'),
        ('job_alert', 'Job Alert'),
        ('saved_search', 'Saved Search Match'),
        ('message', 'Message'),
        ('system', 'System Notification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class Company(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True)
    location = models.CharField(max_length=200)
    industry = models.CharField(max_length=100)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

class Employer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='myapp_employer')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employers')
    job_title = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    is_primary_contact = models.BooleanField(default=False)
    can_post_jobs = models.BooleanField(default=True)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='PH')
    credentials = models.TextField(blank=True, help_text='List your credentials, certifications, or awards.')
    resume = models.FileField(upload_to='employer_resumes/', blank=True, null=True, help_text='Upload your resume (PDF, DOCX, etc.)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notification preferences
    notify_new_applications = models.BooleanField(default=True, help_text='Receive notifications about new job applications')
    notify_messages = models.BooleanField(default=True, help_text='Receive notifications about new messages')
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name}"
    
    class Meta:
        indexes = [
            models.Index(fields=['is_primary_contact']),
            models.Index(fields=['can_post_jobs']),
        ]

class JobSeeker(models.Model):
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive Level'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='myapp_jobseeker')
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default='PH')
    bio = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    preferred_job_types = models.CharField(max_length=200, blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES)
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    preferred_locations = models.TextField(blank=True)
    professional_summary = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notification preferences
    notify_application_status = models.BooleanField(default=True, help_text='Receive notifications about application status changes')
    notify_job_alerts = models.BooleanField(default=True, help_text='Receive notifications about new job matches')
    notify_saved_searches = models.BooleanField(default=True, help_text='Receive notifications about saved search results')
    notify_messages = models.BooleanField(default=True, help_text='Receive notifications about new messages')
    
    def __str__(self):
        return f"{self.user.username}'s Job Seeker Profile"

    def get_matching_jobs(self, min_score=60):
        matching_jobs = []
        active_jobs = JobPosting.objects.filter(is_active=True)
        
        for job in active_jobs:
            match_data = job.calculate_match_score(self)
            if match_data['total_score'] >= min_score:
                matching_jobs.append({
                    'job': job,
                    'match_data': match_data
                })
        
        return sorted(matching_jobs, key=lambda x: x['match_data']['total_score'], reverse=True)

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewing', 'Reviewing'),
        ('shortlisted', 'Shortlisted'),
        ('interviewing', 'Interviewing'),
        ('offered', 'Offered'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    job = models.ForeignKey('JobPosting', on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey('JobSeeker', on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    match_score = models.FloatField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    def __str__(self):
        return f"{self.applicant.user.username}'s application for {self.job.title}"

    class Meta:
        ordering = ['-applied_at']
        unique_together = ['job', 'applicant']

    def save(self, *args, **kwargs):
        if not self.match_score:
            self.match_score = self.job.calculate_match_score(self.applicant)['total_score']
        
        # Create status history entry if status has changed
        if self.pk is None or self.status != self._original_status:
            super().save(*args, **kwargs)  # Save first to ensure we have a PK
            ApplicationStatusHistory.objects.create(
                application=self,
                status=self.status,
                changed_by=None,  # Set to None since we don't have access to request.user
                notes='Status updated'
            )
            self._original_status = self.status
        else:
            super().save(*args, **kwargs)

class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=JobApplication.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.application} - {self.status} at {self.changed_at}"

    class Meta:
        verbose_name_plural = "Application Status Histories"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['application']),
            models.Index(fields=['status']),
            models.Index(fields=['changed_at']),
        ]

class JobAlert(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ]

    job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, related_name='job_alerts')
    keywords = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JobPosting.JOB_TYPE_CHOICES, blank=True)
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.job_seeker.user.get_full_name()} - {self.keywords}"

class SavedJob(models.Model):
    job_seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('job_seeker', 'job')

    def __str__(self):
        return f"{self.job_seeker.user.get_full_name()} - {self.job.title}"

class JobMatch(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='matches')
    jobseeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, related_name='job_matches')
    match_score = models.FloatField()
    skill_match = models.FloatField()
    experience_match = models.FloatField()
    salary_match = models.FloatField()
    location_match = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.jobseeker.user.get_full_name()} - {self.job.title} ({self.match_score}%)"

    class Meta:
        ordering = ['-match_score']
        unique_together = ('job', 'jobseeker')
        indexes = [
            models.Index(fields=['job', 'match_score']),
            models.Index(fields=['jobseeker', 'match_score']),
        ]

    def calculate_match(self):
        match_data = self.job.calculate_match_score(self.jobseeker)
        self.match_score = match_data['total_score']
        self.skill_match = match_data['skill_match']
        self.experience_match = match_data['experience_match']
        self.salary_match = match_data['salary_match']
        self.location_match = match_data['location_match']
        self.save()

class SearchLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='myapp_searchlogs')
    query = models.CharField(max_length=200)
    filters = models.JSONField(default=dict)
    results_count = models.IntegerField()
    searched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.query}"

class SavedSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='myapp_saved_searches')
    name = models.CharField(max_length=100)
    query = models.CharField(max_length=200)
    filters = models.JSONField(default=dict)
    notification_frequency = models.CharField(max_length=20, choices=JobAlert.FREQUENCY_CHOICES, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_notification_sent = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

    class Meta:
        verbose_name_plural = "Saved Searches"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

class JobViewLog(models.Model):
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='view_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='myapp_viewlogs')
    session_id = models.CharField(max_length=100)
    source = models.CharField(max_length=100, blank=True)
    ip_address = models.CharField(max_length=45, blank=True)  # IPv6 addresses can be up to 45 chars
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(max_length=500, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.job.title}"

    class Meta:
        indexes = [
            models.Index(fields=['job']),
            models.Index(fields=['user']),
            models.Index(fields=['viewed_at']),
        ]

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='myapp_sessions')
    session_key = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True)
    pages_viewed = models.IntegerField(default=0)
    actions_performed = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} - {self.start_time}"

class PageView(models.Model):
    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    page_url = models.URLField()
    view_time = models.DateTimeField(auto_now_add=True)
    time_spent = models.DurationField(null=True)
    referrer = models.URLField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['page_url', 'view_time']),
        ]

    def __str__(self):
        return f"{self.session.user.username} - {self.page_url}"

class UserAction(models.Model):
    ACTION_TYPES = [
        ('search', 'Search'),
        ('apply', 'Apply'),
        ('save', 'Save Job'),
        ('view', 'View Job'),
        ('download', 'Download'),
        ('share', 'Share'),
    ]

    session = models.ForeignKey(UserSession, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_time = models.DateTimeField(auto_now_add=True)
    action_data = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=['action_type', 'action_time']),
        ]

    def __str__(self):
        return f"{self.session.user.username} - {self.action_type}"

class AnalyticsReport(models.Model):
    REPORT_TYPES = [
        ('user_engagement', 'User Engagement'),
        ('job_performance', 'Job Performance'),
        ('application_funnel', 'Application Funnel'),
        ('platform_metrics', 'Platform Metrics'),
        ('custom', 'Custom Report'),
    ]

    FREQUENCIES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='myapp_created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    last_generated = models.DateTimeField(null=True)
    schedule_frequency = models.CharField(max_length=20, choices=FREQUENCIES, null=True)
    recipients = models.ManyToManyField(User, related_name='myapp_subscribed_reports')
    parameters = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['report_type', 'created_at']),
            models.Index(fields=['created_by', 'is_active']),
        ]

    def __str__(self):
        return self.name

    def generate_report(self):
        """Generate report based on type and parameters"""
        from .analytics import AnalyticsManager
        
        days = self.parameters.get('days', 30)
        
        if self.report_type == 'user_engagement':
            return AnalyticsManager.get_user_engagement_metrics(
                user=self.created_by,
                days=days
            )
        elif self.report_type == 'job_performance':
            job_ids = self.parameters.get('job_ids')
            return {
                'metrics': AnalyticsManager.get_job_performance_metrics(
                    job_ids=job_ids,
                    days=days
                )
            }
        elif self.report_type == 'application_funnel':
            return AnalyticsManager.get_application_funnel_metrics(days=days)
        elif self.report_type == 'platform_metrics':
            return AnalyticsManager.get_platform_metrics(days=days)
        elif self.report_type == 'custom':
            # Custom reports can combine multiple metrics
            metrics = {}
            if self.parameters.get('include_user_engagement'):
                metrics['user_engagement'] = AnalyticsManager.get_user_engagement_metrics(
                    user=self.created_by,
                    days=days
                )
            if self.parameters.get('include_job_performance'):
                metrics['job_performance'] = AnalyticsManager.get_job_performance_metrics(
                    job_ids=self.parameters.get('job_ids'),
                    days=days
                )
            if self.parameters.get('include_funnel'):
                metrics['funnel'] = AnalyticsManager.get_application_funnel_metrics(days=days)
            if self.parameters.get('include_platform'):
                metrics['platform'] = AnalyticsManager.get_platform_metrics(days=days)
            return metrics
            
        return {}

class ApplicationHistory(models.Model):
    application = models.ForeignKey('JobApplication', on_delete=models.CASCADE, related_name='history')
    status = models.CharField(max_length=20, choices=JobApplication.STATUS_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name_plural = "Application History"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application} - {self.status} at {self.created_at}"
