from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail

from myapp.models import (
    JobCategory, Skill, Benefit, JobPosting, Company,
    JobMetrics, JobSeeker, Employer, JobApplication,
    SavedJob, JobAlert, Notification, JobMatch,
    SavedSearch, ApplicationStatusHistory, JobViewLog
)
from jobs.forms import (
    JobPostingForm, JobSeekerProfileForm, EmployerProfileForm,
    ApplicationForm, JobSeekerRegistrationForm, EmployerRegistrationForm
)

class BaseTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.job_seeker_user = User.objects.create_user(
            username='jobseeker',
            email='jobseeker@example.com',
            password='testpass123'
        )
        
        self.employer_user = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='testpass123'
        )
        
        # Create job seeker profile only if it doesn't exist
        self.job_seeker, created = JobSeeker.objects.get_or_create(
            user=self.job_seeker_user,
            defaults={
                'experience_level': 'entry',
                'location': 'Test City'
            }
        )
        
        # Create test data
        self.category = JobCategory.objects.create(name='Test Category')
        self.skill = Skill.objects.create(name='Test Skill')
        self.benefit = Benefit.objects.create(name='Test Benefit')
        
        # Create company and employer
        self.company = Company.objects.create(
            name='Test Company',
            description='Test Description',
            website='http://test.com',
            location='Test City'
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            company=self.company
        )

class ModelTests(BaseTestCase):
    def test_job_posting_creation(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            requirements='Test Requirements',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30),
            salary_min=50000,
            salary_max=70000
        )
        job.required_skills.add(self.skill)
        job.benefits.add(self.benefit)
        
        self.assertEqual(str(job), f"{job.title} at {job.company.name}")
        self.assertEqual(job.required_skills.count(), 1)
        self.assertEqual(job.benefits.count(), 1)
        self.assertTrue(job.is_active)
        self.assertFalse(job.is_featured)
    
    def test_job_application_creation(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            requirements='Test Requirements',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30)
        )
        
        application = JobApplication.objects.create(
            job=job,
            applicant=self.job_seeker,
            cover_letter='Test Cover Letter',
            status='pending'
        )
        
        self.assertEqual(str(application), f"{self.job_seeker.user.username}'s application for {job.title}")
        self.assertEqual(application.status, 'pending')

class FormTests(BaseTestCase):
    def test_job_posting_form(self):
        form_data = {
            'title': 'Test Job',
            'description': 'Test Description',
            'requirements': 'Test Requirements',
            'company': self.company.id,
            'category': self.category.id,
            'job_type': 'full_time',
            'experience_level': 'entry',
            'location': 'Test City',
            'application_deadline': (timezone.now() + timezone.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S'),
            'salary_min': 50000,
            'salary_max': 70000,
            'required_skills': [self.skill.id],
            'cost_per_day': 100.00
        }
        form = JobPostingForm(data=form_data)
        if not form.is_valid():
            print("Form errors:", form.errors)
        self.assertTrue(form.is_valid())
    
    def test_job_application_form(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30)
        )
        
        form_data = {
            'job': job.id,
            'cover_letter': 'Test Cover Letter'
        }
        form = ApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())

class ViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        # Create a request object for authentication
        self.request = self.client.request().wsgi_request
        # Force login instead of using client.login
        self.client.force_login(self.job_seeker_user)
    
    def test_job_list_view(self):
        response = self.client.get(reverse('jobs:job_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_job_detail_view(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            requirements='Test Requirements',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30)
        )
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))
        self.assertEqual(response.status_code, 200)
    
    def test_job_application_view(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            requirements='Test Requirements',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30)
        )
        response = self.client.post(reverse('jobs:job_apply', args=[job.id]), {
            'cover_letter': 'Test Cover Letter'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful application

class APITests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        # Create a request object for authentication
        self.request = self.client.request().wsgi_request
        # Force login instead of using client.login
        self.client.force_login(self.job_seeker_user)
    
    def test_job_posting_api(self):
        data = {
            'title': 'Test Job',
            'description': 'Test Description',
            'requirements': 'Test Requirements',
            'company_id': self.company.id,
            'category_id': self.category.id,
            'job_type': 'full_time',
            'experience_level': 'entry',
            'location': 'Test City',
            'application_deadline': (timezone.now() + timezone.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S'),
            'salary_min': 50000,
            'salary_max': 70000,
            'required_skills_ids': [self.skill.id],
            'preferred_skills_ids': [],
            'benefits_ids': []
        }
        response = self.client.post('/api/job-postings/', data)
        self.assertEqual(response.status_code, 201)
    
    def test_job_application_api(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            requirements='Test Requirements',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30)
        )
        
        data = {
            'job_id': job.id,
            'applicant_id': self.job_seeker.id,
            'cover_letter': 'Test Cover Letter',
            'status': 'pending'
        }
        response = self.client.post('/api/job-applications/', data)
        self.assertEqual(response.status_code, 201)

class IntegrationTests(BaseTestCase):
    def test_job_application_flow(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            requirements='Test Requirements',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30)
        )
        
        # Apply for job
        application = JobApplication.objects.create(
            job=job,
            applicant=self.job_seeker,
            cover_letter='Test Cover Letter'
        )
        
        # Update application status
        application.status = 'reviewing'
        application.save()
        
        # Verify status history
        self.assertEqual(application.status_history.count(), 2)  # Should have two entries - initial pending and reviewing
        self.assertEqual(application.status_history.first().status, 'reviewing')  # Most recent status
        self.assertEqual(application.status_history.last().status, 'pending')  # Initial status

class SecurityTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        # Create a request object for authentication
        self.request = self.client.request().wsgi_request
    
    def test_unauthorized_access(self):
        job = JobPosting.objects.create(
            title='Test Job',
            description='Test Description',
            requirements='Test Requirements',
            company=self.company,
            category=self.category,
            job_type='full_time',
            experience_level='entry',
            location='Test City',
            application_deadline=timezone.now() + timezone.timedelta(days=30)
        )
        response = self.client.get(reverse('jobs:job_detail', args=[job.id]))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
    
    def test_employer_permissions(self):
        response = self.client.get(reverse('jobs:employer_dashboard'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
