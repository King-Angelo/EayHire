from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, DeleteView, View
from django.urls import reverse_lazy
from django.db.models import Count, Q, F, FloatField, Avg, Sum, Case, When
from django.db.models.functions import ExtractMonth, Trunc, TruncDate
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import DateTimeField
from django.contrib.auth.models import User
from myapp.models import (
    JobPosting, JobSeeker, Employer, JobApplication, SavedJob, Skill, JobAlert, 
    ApplicationStatusHistory, SavedSearch, SearchLog, JobMetrics, JobViewLog, 
    Notification, JobMatch, AnalyticsReport, Company
)
from .forms import (
    JobSeekerProfileForm, EmployerProfileForm, JobPostingForm, ApplicationForm, 
    EmployerRegistrationForm, JobSeekerRegistrationForm, JobAlertForm, 
    ApplicationUpdateForm, ApplicationStatusUpdateForm
)
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import login
from django.core.mail import send_mail
from django.http import FileResponse, Http404, JsonResponse, HttpResponse, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
import os
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import datetime, timedelta
import logging
from django.contrib.auth.decorators import login_required
import json
from django.utils.decorators import method_decorator
from myapp.analytics import AnalyticsManager
from django.shortcuts import render
from .models import SavedJob
from django.views.decorators.http import require_GET, require_POST

# Create your views here.

class JobListView(ListView):
    model = JobPosting
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 12

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'myapp_employer'):
                return redirect('jobs:employer_dashboard')
            # Jobseekers are allowed to access the job list/search page
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = JobPosting.objects.filter(is_active=True).select_related('company')
        query = self.request.GET.get('q')
        location = self.request.GET.get('location')
        job_type = self.request.GET.get('job_type')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query)
            )
        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add featured jobs to context
        context['featured_jobs'] = JobPosting.objects.filter(
            is_active=True,
            is_featured=True
        ).select_related('company')[:6]
        
        # Add job types for filter dropdown
        context['job_types'] = JobPosting.JOB_TYPE_CHOICES
        
        # Add applied_job_ids for jobseeker
        if self.request.user.is_authenticated and hasattr(self.request.user, 'myapp_jobseeker'):
            from jobs.models import JobApplication
            context['applied_job_ids'] = list(
                JobApplication.objects.filter(applicant=self.request.user.myapp_jobseeker)
                .values_list('job_id', flat=True)
            )
        else:
            context['applied_job_ids'] = []
        
        # Debug: Print context data
        print(f"Context Data: {context}")
        
        return context

class JobDetailView(LoginRequiredMixin, DetailView):
    model = JobPosting
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        job = self.object

        # Initialize default values
        context['can_edit'] = False
        context['can_apply'] = False
        context['has_applied'] = False
        context['is_saved'] = False

        if user.is_authenticated:
            # Check if user is an employer
            if hasattr(user, 'myapp_employer'):
                employer = user.myapp_employer
                # Check if this employer's company owns this job posting
                context['can_edit'] = job.company.id == employer.company.id
            
            # Check if user is a job seeker
            elif hasattr(user, 'myapp_jobseeker'):
                jobseeker = user.myapp_jobseeker
                context['can_apply'] = True
                context['has_applied'] = job.applications.filter(applicant=jobseeker).exists()
                context['is_saved'] = job.saved_by.filter(id=jobseeker.id).exists()
    

        # Get similar jobs
        similar_jobs = JobPosting.objects.filter(
            Q(category=job.category) | 
            Q(job_type=job.job_type)
        ).exclude(id=job.id)[:3]
        context['similar_jobs'] = similar_jobs

        return context

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Log view
        if response.status_code == 200:
            job = self.object
            JobViewLog.objects.create(
                job=job,
                user=request.user if request.user.is_authenticated else None,
                session_id=request.session.session_key or '',
                ip_address=request.META.get('REMOTE_ADDR', ''),
                source=request.GET.get('source', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                referrer=request.META.get('HTTP_REFERER', '')
            )
            
            # Update metrics
            metrics, _ = JobMetrics.objects.get_or_create(job=job)
            metrics.views += 1
            if not JobViewLog.objects.filter(
                job=job,
                session_id=request.session.session_key,
                viewed_at__date=timezone.now().date()
            ).exists():
                metrics.unique_views += 1
            metrics.save()
        
        return response

class JobPostingCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'jobs/job_posting_form.html'
    success_url = reverse_lazy('jobs:employer_jobs')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employer'] = self.request.user.myapp_employer
        return kwargs

    def form_valid(self, form):
        form.instance.company = self.request.user.myapp_employer.company
        return super().form_valid(form)

    def test_func(self):
        return hasattr(self.request.user, 'myapp_employer')
    

class JobSeekerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'jobs/jobseeker_dashboard.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'myapp_jobseeker')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        jobseeker = self.request.user.myapp_jobseeker
        
        # Get application statistics
        applications = JobApplication.objects.filter(applicant=jobseeker)
        context['total_applications'] = applications.count()
        context['pending_applications'] = applications.filter(status='pending').count()
        context['shortlisted_applications'] = applications.filter(status='shortlisted').count()
        context['saved_jobs'] = SavedJob.objects.filter(job_seeker=jobseeker).count()
        
        # Get recent applications
        context['recent_applications'] = applications.order_by('-applied_at')[:5]
        
        # Get all job matches ordered by match score
        all_matches = list(JobMatch.objects.filter(
            jobseeker=jobseeker
        ).order_by('-match_score'))
        # Show all job matches in the dashboard, regardless of score
        context['job_matches'] = all_matches
        context['has_more_job_matches'] = False  # No need for 'View All' if all are shown
        
        # Get saved searches
        context['saved_searches'] = SavedSearch.objects.filter(
            user=jobseeker.user,
            is_active=True
        )
        
        # Get notifications
        context['notifications'] = Notification.objects.filter(
            user=jobseeker.user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        return context

class SavedJobView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = SavedJob
    template_name = 'jobs/savedjob_form.html'
    fields = ['notes']
    success_url = reverse_lazy('jobs:employer_jobs')

    def test_func(self):
        return hasattr(self.request.user, 'myapp_jobseeker')

    def form_valid(self, form):
        job = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        
        # Check if job is already saved
        if SavedJob.objects.filter(
            job_seeker=self.request.user.myapp_jobseeker,
            job=job
        ).exists():
            messages.warning(self.request, 'You have already saved this job.')
            return redirect('jobs:job_detail', pk=job.pk)
            
        form.instance.job_seeker = self.request.user.myapp_jobseeker
        form.instance.job = job
        messages.success(self.request, 'Job saved successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        return context

class ApplicationCreateView(LoginRequiredMixin, CreateView):
    model = JobApplication
    form_class = ApplicationForm
    template_name = 'jobs/application_form.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        return context

    def form_valid(self, form):
        job = get_object_or_404(JobPosting, pk=self.kwargs['job_id'])
        
        # Check if job is expired
        if job.is_expired:
            messages.error(self.request, 'This job posting has expired and is no longer accepting applications.')
            return redirect('jobs:job_detail', pk=job.pk)
        
        # Check if job is inactive
        if not job.is_active:
            messages.error(self.request, 'This job posting is no longer accepting applications.')
            return redirect('jobs:job_detail', pk=job.pk)
        
        # Check if user has already applied
        if JobApplication.objects.filter(
            job_id=self.kwargs['job_id'],
            applicant=self.request.user.myapp_jobseeker
        ).exists():
            messages.error(self.request, 'You have already applied for this job.')
            return redirect('jobs:job_detail', pk=self.kwargs['job_id'])

        form.instance.applicant = self.request.user.myapp_jobseeker
        form.instance.job = job
        return super().form_valid(form)

class ApplicationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = JobApplication
    template_name = 'jobs/application_detail.html'
    context_object_name = 'application'

    def test_func(self):
        # Check if user has required profile
        if not (hasattr(self.request.user, 'myapp_jobseeker') or hasattr(self.request.user, 'myapp_employer')):
            messages.error(self.request, 'You must be registered as a jobseeker or employer to view applications.')
            return False
            
        try:
            application = self.get_object()
            # Allow access if user is the employer of the job or the applicant
            return (
                (hasattr(self.request.user, 'myapp_employer') and 
                 self.request.user.myapp_employer in application.job.company.employers.all()) or
                (hasattr(self.request.user, 'myapp_jobseeker') and 
                 self.request.user.myapp_jobseeker == application.applicant)
            )
        except Http404:
            return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to view application details.')
            return redirect('account_login')
        messages.error(self.request, 'You do not have permission to view this application.')
        return redirect('jobs:employer_jobs')

    def get_queryset(self):
        return JobApplication.objects.select_related(
            'job', 
            'applicant', 
            'applicant__user', 
            'job__company'
        )

class ApplicationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JobApplication
    form_class = ApplicationUpdateForm
    template_name = 'jobs/application_form.html'
    success_url = reverse_lazy('jobs:application_detail')

    def test_func(self):
        application = self.get_object()
        return application.applicant.user == self.request.user

    def get_success_url(self):
        return reverse('jobs:application_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        # Only update resume if a new one is provided
        if not form.cleaned_data['resume']:
            form.instance.resume = self.get_object().resume
        return super().form_valid(form)

class ApplicationStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JobApplication
    form_class = ApplicationStatusUpdateForm
    template_name = 'jobs/application_status_update.html'
    success_url = reverse_lazy('jobs:employer_dashboard')

    def test_func(self):
        if not self.request.user.is_authenticated:
            return False
        if not hasattr(self.request.user, 'myapp_employer'):
            return False
        application = self.get_object()
        return self.request.user.myapp_employer in application.job.company.employers.all()

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to update application status.')
            return redirect('account_login')
        messages.error(self.request, 'You do not have permission to update this application status.')
        return redirect('jobs:employer_dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_history'] = self.object.status_history.all().order_by('-changed_at')
        return context

    def form_valid(self, form):
        form.instance.changed_by = self.request.user
        response = form.save(commit=True, changed_by=self.request.user)
        messages.success(self.request, 'Application status updated successfully.')
        return super().form_valid(form)

class EmployerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/employer/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employer = self.request.user.myapp_employer
        
        # Get all jobs for this employer's company
        jobs = JobPosting.objects.filter(company=employer.company)
        active_jobs = jobs.filter(is_active=True)
        
        # Get recent applications
        recent_applications = JobApplication.objects.filter(
            job__in=jobs
        ).select_related('applicant', 'job').order_by('-applied_at')[:5]
        
        # Get all active job listings with application counts
        active_job_listings = active_jobs.annotate(
            total_applications_count=Count('applications')
        ).order_by('-created_at')
        
        # Update context
        context.update({
            'active_jobs': active_jobs.count(),
            'total_jobs': jobs.count(),
            'active_job_listings': active_job_listings,
            'recent_applications': recent_applications,
            'new_applications': JobApplication.objects.filter(
                job__in=jobs,
                status='pending'
            ).count(),
            'shortlisted_candidates': JobApplication.objects.filter(
                job__in=jobs,
                status='shortlisted'
            ).count(),
        })
        
        # Add notifications
        context['notifications'] = Notification.objects.filter(
            user=self.request.user,
            is_read=False
        ).order_by('-created_at')[:5]
        
        return context

class JobPostingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'jobs/job_posting_form.html'
    success_url = reverse_lazy('jobs:employer_jobs')

    def test_func(self):
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if user is authenticated
        if not self.request.user.is_authenticated:
            logger.warning("User is not authenticated")
            return False
            
        try:
            # Get the employer profile
            if not hasattr(self.request.user, 'myapp_employer'):
                logger.warning("User does not have an employer profile")
                return False
                
            employer = self.request.user.myapp_employer
            logger.info(f"Found employer profile: {employer.id}")
            
            # Get the job posting
            job = self.get_object()
            logger.info(f"Found job posting: {job.id}")
            
            # Check if employer has a company
            if not employer.company:
                logger.warning("Employer does not have a company assigned")
                return False
                
            # Check if job has a company
            if not job.company:
                logger.warning("Job does not have a company assigned")
                return False
            
            # Check if the employer's company matches the job's company
            has_permission = job.company.id == employer.company.id
            logger.info(f"Permission check result: {has_permission}")
            
            return has_permission
            
        except Exception as e:
            logger.error(f"Error in test_func: {str(e)}")
            return False

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Please log in to edit job postings.")
            return redirect('login')
        elif not hasattr(self.request.user, 'myapp_employer'):
            messages.error(self.request, "You must be registered as an employer to edit job postings.")
        else:
            messages.error(self.request, "You do not have permission to edit this job posting. Only employers from the company that created the job posting can edit it.")
        return redirect('jobs:employer_jobs')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['employer'] = self.request.user.myapp_employer
        return kwargs

class JobPostingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = JobPosting
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('jobs:employer_jobs')

    def test_func(self):
        if not hasattr(self.request.user, 'myapp_employer'):
            messages.error(self.request, 'You must be registered as an employer to delete job postings.')
            return False
            
        job = self.get_object()
        employer = self.request.user.myapp_employer
        
        # Check if the job belongs to the employer's company
        return job.company == employer.company

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to delete job postings.')
            return redirect('account_login')
        messages.error(self.request, 'You do not have permission to delete this job posting.')
        return redirect('jobs:employer_jobs')

    def delete(self, request, *args, **kwargs):
        job = self.get_object()
        messages.success(request, f'Job posting "{job.title}" has been successfully deleted.')
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['applications_count'] = JobApplication.objects.filter(job=self.object).count()
        return context

class JobToggleStatusView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        if not hasattr(self.request.user, 'myapp_employer'):
            messages.error(self.request, 'You must be registered as an employer to manage job postings.')
            return False
            
        job = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        employer = self.request.user.myapp_employer
        
        # Check if the job belongs to the employer's company
        return job.company == employer.company

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, 'Please log in to manage job postings.')
            return redirect('account_login')
        messages.error(self.request, 'You do not have permission to manage this job posting.')
        return redirect('jobs:employer_jobs')

    def post(self, request, pk):
        job = get_object_or_404(JobPosting, pk=pk)
        job.is_active = not job.is_active
        job.save()
        messages.success(request, f'Job "{job.title}" has been {"activated" if job.is_active else "deactivated"}.')
        return redirect('jobs:job_detail', pk=job.pk)

def home(request):
    jobs = JobPosting.objects.filter(
        is_active=True,
        application_deadline__gte=timezone.now()
    )
    query = (request.GET.get('q') or '').strip()
    location = (request.GET.get('location') or '').strip()
    job_type = (request.GET.get('job_type') or '').strip()

    # Only filter if the value is not empty after stripping
    if query or location or job_type:
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query)
            )
        if location:
            jobs = jobs.filter(location__icontains=location)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        jobs = jobs.order_by('-created_at')
    else:
        jobs = jobs.order_by('-created_at')[:5]  # Only slice after ordering

    return render(request, 'jobs/home.html', {'jobs': jobs})

class EmployerRegistrationView(CreateView):
    form_class = EmployerRegistrationForm
    template_name = 'jobs/employer_registration.html'
    success_url = reverse_lazy('jobs:employer_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already logged in and has an employer profile, redirect to dashboard
        if request.user.is_authenticated and hasattr(request.user, 'myapp_employer'):
            messages.info(request, 'You are already registered as an employer.')
            return redirect('jobs:employer_dashboard')
            
        # If user is already a job seeker, show an error
        if request.user.is_authenticated and hasattr(request.user, 'myapp_jobseeker'):
            messages.error(request, 'You are already registered as a job seeker. Please use a different account to register as an employer.')
            return redirect('jobs:home')
            
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # If user is not already logged in, log them in
        if not self.request.user.is_authenticated:
            # Set the backend and login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            
        messages.success(self.request, 'Employer account created successfully!')
        return response

class JobSeekerRegistrationView(CreateView):
    form_class = JobSeekerRegistrationForm
    template_name = 'jobs/jobseeker_registration.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')
    
    def dispatch(self, request, *args, **kwargs):
        # If user is already logged in and has a job seeker profile, redirect to dashboard
        if request.user.is_authenticated and hasattr(request.user, 'myapp_jobseeker'):
            messages.info(request, 'You are already registered as a job seeker.')
            return redirect('jobs:jobseeker_dashboard')
            
        # If user is already an employer, show an error
        if request.user.is_authenticated and hasattr(request.user, 'myapp_employer'):
            messages.error(request, 'You are already registered as an employer. Please use a different account to register as a job seeker.')
            return redirect('jobs:home')
            
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.save()
        
        # If user is not already logged in, log them in
        if not self.request.user.is_authenticated:
            # Set the backend and login
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            
        messages.success(self.request, 'Job seeker account created successfully!')
        return response

class SavedJobListView(LoginRequiredMixin, ListView):
    model = SavedJob
    template_name = 'jobs/saved_jobs.html'
    context_object_name = 'saved_jobs'

    def get_queryset(self):
        return SavedJob.objects.filter(
            job_seeker=self.request.user.myapp_jobseeker
        ).order_by('-saved_at')
    
class JobSeekerProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = JobSeeker
    form_class = JobSeekerProfileForm
    template_name = 'jobs/jobseeker_profile_form.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')

    def get_object(self, queryset=None):
        return self.request.user.myapp_jobseeker

    def form_valid(self, form):
        # Print form data and current object state
        print("Form data:", form.cleaned_data)
        print("Current location:", self.get_object().location)
        
        # Save the form
        response = super().form_valid(form)
        
        # Print the new object state
        print("New location:", self.get_object().location)
        
        messages.success(self.request, 'Profile updated successfully!')
        return response

    def get_initial(self):
        # Get the current values
        initial = super().get_initial()
        jobseeker = self.get_object()
        print("Initial location:", jobseeker.location)
        return initial

class JobAlertListView(LoginRequiredMixin, ListView):
    model = JobAlert
    template_name = 'jobs/job_alert_list.html'
    context_object_name = 'alerts'

    def get_queryset(self):
        return JobAlert.objects.filter(job_seeker=self.request.user.myapp_jobseeker).order_by('-created_at')

class JobAlertCreateView(LoginRequiredMixin, CreateView):
    model = JobAlert
    form_class = JobAlertForm
    template_name = 'jobs/job_alert_form.html'
    success_url = reverse_lazy('jobs:job_alert_list')

    def form_valid(self, form):
        form.instance.job_seeker = self.request.user.myapp_jobseeker
        return super().form_valid(form)

class JobAlertUpdateView(LoginRequiredMixin, UpdateView):
    model = JobAlert
    form_class = JobAlertForm
    template_name = 'jobs/job_alert_form.html'
    success_url = reverse_lazy('jobs:job_alert_list')

    def get_queryset(self):
        return JobAlert.objects.filter(job_seeker=self.request.user.myapp_jobseeker)

class JobAlertDeleteView(LoginRequiredMixin, DeleteView):
    model = JobAlert
    template_name = 'jobs/job_alert_confirm_delete.html'
    success_url = reverse_lazy('jobs:job_alert_list')

    def get_queryset(self):
        return JobAlert.objects.filter(job_seeker=self.request.user.myapp_jobseeker)

class JobAlertToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        try:
            alert = JobAlert.objects.get(pk=pk, job_seeker=request.user.myapp_jobseeker)
            alert.is_active = not alert.is_active
            alert.save()
            return JsonResponse({
                'status': 'success',
                'is_active': alert.is_active
            })
        except JobAlert.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Alert not found'
            }, status=404)

class ResumeView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        application = get_object_or_404(JobApplication, pk=self.kwargs['application_id'])
        # Allow access if user is the employer of the job or the applicant
        return (
            hasattr(self.request.user, 'myapp_employer') and 
            self.request.user.myapp_employer in application.job.company.employers.all()
        ) or (
            hasattr(self.request.user, 'myapp_jobseeker') and 
            self.request.user.myapp_jobseeker == application.applicant
        )

    def get(self, request, application_id):
        application = get_object_or_404(JobApplication, pk=application_id)
        
        if not application.resume:
            raise Http404("No resume found for this application")
        
        try:
            resume_path = application.resume.path
            if not os.path.exists(resume_path):
                raise Http404("Resume file not found")
            
            # Get the file extension
            file_ext = os.path.splitext(resume_path)[1].lower()
            
            # Set the content type based on file extension
            content_type = {
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.txt': 'text/plain'
            }.get(file_ext, 'application/octet-stream')
            
            # Determine if we should force download or display inline
            disposition = 'attachment' if request.GET.get('download') == 'true' else 'inline'
            
            response = FileResponse(open(resume_path, 'rb'), content_type=content_type)
            response['Content-Disposition'] = f'{disposition}; filename="{os.path.basename(resume_path)}"'
            return response
            
        except Exception as e:
            raise Http404(f"Error accessing resume file: {str(e)}")

class BulkStatusUpdateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return hasattr(self.request.user, 'myapp_employer')
    
    def post(self, request):
        application_ids = request.POST.get('application_ids', '').split(',')
        status = request.POST.get('status')
        
        if not application_ids or not status:
            messages.error(request, 'Invalid request parameters')
            return redirect('jobs:employer_dashboard')
            
        # Get applications that belong to this employer
        applications = JobApplication.objects.filter(
            id__in=application_ids,
            job__company=request.user.myapp_employer.company
        )
        
        # Update status and create history entries
        updated_count = 0
        for application in applications:
            if application.status != status:
                # Create history entry
                ApplicationStatusHistory.objects.create(
                    application=application,
                    old_status=application.status,
                    new_status=status,
                    changed_by=request.user,
                    comments=f"Status updated via bulk action by {request.user.get_full_name() or request.user.username}"
                )
                
                # Update application status
                application.status = status
                application.save()
                
                # Send email notification
                subject = f'Your application status has been updated - {application.job.title}'
                message = f'''Dear {application.applicant.user.get_full_name() or application.applicant.user.username},

Your application for the position of {application.job.title} at {application.job.company.name} has been updated.

New Status: {application.get_status_display()}

Best regards,
{application.job.company.name} Team
'''
                try:
                    send_mail(
                        subject,
                        message,
                        None,  # Use default from email
                        [application.applicant.user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Failed to send email: {e}")
                
                updated_count += 1
        
        messages.success(request, f'Successfully updated {updated_count} application(s)')
        return redirect('jobs:employer_dashboard')

class SaveSearchView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'myapp_jobseeker'):
            return JsonResponse({'error': 'Only jobseekers can save searches'}, status=403)

        data = json.loads(request.body)
        title = data.get('title')
        search_params = data.get('search_params')
        email_notifications = data.get('email_notifications', False)

        if not title or not search_params:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        SavedSearch.objects.create(
            jobseeker=request.user.myapp_jobseeker,
            title=title,
            search_params=search_params,
            email_notifications=email_notifications
        )

        return JsonResponse({'message': 'Search saved successfully'})

class DeleteSavedSearchView(LoginRequiredMixin, View):
    def delete(self, request, search_id, *args, **kwargs):
        if not hasattr(request.user, 'myapp_jobseeker'):
            return JsonResponse({'error': 'Only jobseekers can delete saved searches'}, status=403)

        try:
            saved_search = SavedSearch.objects.get(
                id=search_id,
                jobseeker=request.user.myapp_jobseeker
            )
            saved_search.delete()
            return JsonResponse({'message': 'Search deleted successfully'})
        except SavedSearch.DoesNotExist:
            return JsonResponse({'error': 'Saved search not found'}, status=404)

class SaveJobView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, 'myapp_jobseeker'):
            return JsonResponse({'error': 'Only jobseekers can save jobs'}, status=403)

        job_id = request.POST.get('job_id')
        # Only try to parse JSON if the content type is JSON
        if not job_id and request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                job_id = data.get('job_id')
            except Exception:
                job_id = None

        if not job_id:
            return JsonResponse({'error': 'Job ID is required'}, status=400)

        try:
            job = JobPosting.objects.get(id=job_id)
            from jobs.models import SavedJob
            # Prevent duplicate saved jobs
            if not SavedJob.objects.filter(job_seeker=request.user.myapp_jobseeker, job=job).exists():
                SavedJob.objects.create(job_seeker=request.user.myapp_jobseeker, job=job)
            # If AJAX, return JSON
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
                return JsonResponse({'message': 'Job saved successfully'})
            # If regular form POST, redirect back to job detail or referring page
            from django.urls import reverse
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('jobs:job_detail', args=[job_id])))
        except JobPosting.DoesNotExist:
            return JsonResponse({'error': 'Job not found'}, status=404)

class NotificationMarkReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        notification_ids = request.POST.getlist('notification_ids[]')
        mark_all = request.POST.get('mark_all') == 'true'
        
        if mark_all:
            request.user.notifications.filter(is_read=False).update(
                is_read=True,
                read_at=timezone.now()
            )
        elif notification_ids:
            request.user.notifications.filter(id__in=notification_ids).update(
                is_read=True,
                read_at=timezone.now()
            )
        
        return JsonResponse({'status': 'success'})

class AdminAnalyticsDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'jobs/admin_analytics_dashboard.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from request
        date_range = self.request.GET.get('date_range', '30')  # Default to 30 days
        days = int(date_range)
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get user counts and growth
        total_users = User.objects.count()
        previous_users = User.objects.filter(
            date_joined__lt=start_date
        ).count()
        user_growth = ((total_users - previous_users) / previous_users * 100 
                      if previous_users > 0 else 0)
        
        # Get active jobs and applications
        active_jobs = JobPosting.objects.filter(is_active=True).count()
        jobs_this_month = JobPosting.objects.filter(
            created_at__gte=start_date
        ).count()
        
        total_applications = JobApplication.objects.count()
        successful_applications = JobApplication.objects.filter(
            status='accepted'
        ).count()
        application_rate = (successful_applications / total_applications * 100 
                          if total_applications > 0 else 0)
        
        # Calculate engagement score
        engagement_metrics = AnalyticsManager.get_platform_metrics(days=days)
        
        # Prepare metrics context
        context['metrics'] = {
            'total_users': total_users,
            'user_growth': round(user_growth, 1),
            'active_jobs': active_jobs,
            'jobs_this_month': jobs_this_month,
            'total_applications': total_applications,
            'application_rate': round(application_rate, 1),
            'engagement_score': round(engagement_metrics['engagement_score'], 1),
            'engagement_growth': round(engagement_metrics['engagement_growth'], 1)
        }
        
        # Get user growth data
        user_growth_data = AnalyticsManager.get_trend_analysis(
            User,
            'date_joined',
            ['is_staff'],
            days=days
        )
        
        # Prepare chart data
        context['user_growth_data'] = {
            'labels': [d['date'].strftime('%Y-%m-%d') for d in user_growth_data],
            'job_seekers': [d['count'] for d in user_growth_data if not d['is_staff']],
            'employers': [d['count'] for d in user_growth_data if d['is_staff']]
        }
        
        # Get user distribution
        job_seekers = JobSeeker.objects.count()
        employers = Company.objects.count()
        admins = User.objects.filter(is_staff=True).count()
        context['user_distribution'] = [job_seekers, employers, admins]
        
        # Get application success rate over time
        application_success = AnalyticsManager.get_trend_analysis(
            JobApplication,
            'applied_at',
            ['status'],
            days=days
        )
        context['application_success'] = {
            'labels': [d['date'].strftime('%Y-%m-%d') for d in application_success],
            'data': [
                d['count'] / total_applications * 100 
                for d in application_success if d['status'] == 'accepted'
            ]
        }
        
        # Get job categories distribution
        job_categories = (
            JobPosting.objects
            .values('category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        context['job_categories'] = {
            'labels': [c['category'] for c in job_categories],
            'data': [c['count'] for c in job_categories]
        }
        
        # Get scheduled reports
        context['scheduled_reports'] = AnalyticsReport.objects.filter(
            is_active=True
        ).order_by('-created_at')
        
        context['date_range'] = date_range
        return context

class CreateAnalyticsReportView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = AnalyticsReport
    fields = ['name', 'description', 'report_type', 'schedule_frequency', 'parameters']
    template_name = 'jobs/analytics_report_form.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Report created successfully.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs'] = JobPosting.objects.filter(is_active=True).order_by('-created_at')
        return context
    
    def get_success_url(self):
        return reverse('jobs:admin_analytics')

class EditAnalyticsReportView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = AnalyticsReport
    fields = ['name', 'description', 'report_type', 'schedule_frequency', 'parameters', 'is_active']
    template_name = 'jobs/analytics_report_form.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Report updated successfully.')
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs'] = JobPosting.objects.filter(is_active=True).order_by('-created_at')
        return context
    
    def get_success_url(self):
        return reverse('jobs:admin_analytics')

class DeleteAnalyticsReportView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = AnalyticsReport
    template_name = 'jobs/analytics_report_confirm_delete.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Report deleted successfully.')
        return super().delete(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('jobs:admin_analytics')

class DownloadAnalyticsReportView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = AnalyticsReport
    
    def test_func(self):
        return self.request.user.is_staff
    
    def render_to_response(self, context):
        report = self.get_object()
        data = report.generate_report()
        
        # Create Excel file
        import xlsxwriter
        from io import BytesIO
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#3b82f6',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1
        })
        
        percent_format = workbook.add_format({
            'border': 1,
            'num_format': '0.00%'
        })
        
        if report.report_type == 'job_performance':
            worksheet = workbook.add_worksheet('Job Performance')
            headers = ['Job Title', 'Views', 'Applications', 'Conversion Rate', 'Success Rate', 
                      'Cost per Application', 'Time to Fill', 'Top Sources']
            
            # Write headers
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
                
            # Write data
            for row, job in enumerate(data['metrics'], start=1):
                worksheet.write(row, 0, job['job_title'], cell_format)
                worksheet.write(row, 1, job['views'], cell_format)
                worksheet.write(row, 2, job['applications'], cell_format)
                worksheet.write(row, 3, job['conversion_rate'] / 100, percent_format)
                worksheet.write(row, 4, job['success_rate'] / 100, percent_format)
                worksheet.write(row, 5, job['cost_per_application'], cell_format)
                worksheet.write(row, 6, job['time_to_fill'] or 'N/A', cell_format)
                worksheet.write(row, 7, ', '.join(f"{k}: {v}" for k, v in job['source_distribution'].items()), cell_format)
                
        elif report.report_type == 'application_funnel':
            worksheet = workbook.add_worksheet('Application Funnel')
            
            # Funnel stages
            worksheet.write(0, 0, 'Funnel Stages', header_format)
            stages = data['funnel_stages']
            for row, (stage, value) in enumerate(stages.items(), start=1):
                worksheet.write(row, 0, stage.replace('_', ' ').title(), cell_format)
                worksheet.write(row, 1, value, cell_format)
                
            # Conversion rates
            worksheet.write(4, 0, 'Conversion Rates', header_format)
            rates = data['conversion_rates']
            for row, (rate, value) in enumerate(rates.items(), start=5):
                worksheet.write(row, 0, rate.replace('_', ' ').title(), cell_format)
                worksheet.write(row, 1, value / 100, percent_format)
                
            # Status distribution
            worksheet.write(8, 0, 'Status Distribution', header_format)
            statuses = data['status_distribution']
            for row, (status, count) in enumerate(statuses.items(), start=9):
                worksheet.write(row, 0, status.title(), cell_format)
                worksheet.write(row, 1, count, cell_format)
                
        elif report.report_type == 'custom':
            for metric_type, metric_data in data.items():
                worksheet = workbook.add_worksheet(metric_type.replace('_', ' ').title())
                
                # Write metric data based on type
                if metric_type == 'user_engagement':
                    headers = ['Metric', 'Value']
                    worksheet.write_row(0, 0, headers, header_format)
                    for row, (key, value) in enumerate(metric_data.items(), start=1):
                        worksheet.write(row, 0, key.replace('_', ' ').title(), cell_format)
                        worksheet.write(row, 1, value, cell_format)
                        
                elif metric_type == 'job_performance':
                    self._write_job_performance_data(worksheet, metric_data['metrics'], header_format, cell_format, percent_format)
                    
                elif metric_type == 'funnel':
                    self._write_funnel_data(worksheet, metric_data, header_format, cell_format, percent_format)
                    
                elif metric_type == 'platform':
                    headers = ['Metric', 'Value']
                    worksheet.write_row(0, 0, headers, header_format)
                    for row, (key, value) in enumerate(metric_data.items(), start=1):
                        worksheet.write(row, 0, key.replace('_', ' ').title(), cell_format)
                        worksheet.write(row, 1, value if not isinstance(value, dict) else str(value), cell_format)
                        
        else:  # Default handling for other report types
            worksheet = workbook.add_worksheet('Report Data')
            headers = list(data.keys())
            worksheet.write_row(0, 0, headers, header_format)
            for col, header in enumerate(headers):
                value = data[header]
                worksheet.write(1, col, value if not isinstance(value, dict) else str(value), cell_format)
        
        # Auto-adjust column widths
        for worksheet in workbook.worksheets():
            worksheet.autofit()
        
        workbook.close()
        output.seek(0)
        
        # Create response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{report.name}.xlsx"'
        
        return response
        
    def _write_job_performance_data(self, worksheet, data, header_format, cell_format, percent_format):
        headers = ['Job Title', 'Views', 'Applications', 'Conversion Rate', 'Success Rate', 
                  'Cost per Application', 'Time to Fill', 'Top Sources']
        worksheet.write_row(0, 0, headers, header_format)
        
        for row, job in enumerate(data, start=1):
            worksheet.write(row, 0, job['job_title'], cell_format)
            worksheet.write(row, 1, job['views'], cell_format)
            worksheet.write(row, 2, job['applications'], cell_format)
            worksheet.write(row, 3, job['conversion_rate'] / 100, percent_format)
            worksheet.write(row, 4, job['success_rate'] / 100, percent_format)
            worksheet.write(row, 5, job['cost_per_application'], cell_format)
            worksheet.write(row, 6, job['time_to_fill'] or 'N/A', cell_format)
            worksheet.write(row, 7, ', '.join(f"{k}: {v}" for k, v in job['source_distribution'].items()), cell_format)
            
    def _write_funnel_data(self, worksheet, data, header_format, cell_format, percent_format):
        # Funnel stages
        worksheet.write(0, 0, 'Funnel Stages', header_format)
        stages = data['funnel_stages']
        for row, (stage, value) in enumerate(stages.items(), start=1):
            worksheet.write(row, 0, stage.replace('_', ' ').title(), cell_format)
            worksheet.write(row, 1, value, cell_format)
            
        # Conversion rates
        worksheet.write(4, 0, 'Conversion Rates', header_format)
        rates = data['conversion_rates']
        for row, (rate, value) in enumerate(rates.items(), start=5):
            worksheet.write(row, 0, rate.replace('_', ' ').title(), cell_format)
            worksheet.write(row, 1, value / 100, percent_format)
            
        # Status distribution
        worksheet.write(8, 0, 'Status Distribution', header_format)
        statuses = data['status_distribution']
        for row, (status, count) in enumerate(statuses.items(), start=9):
            worksheet.write(row, 0, status.title(), cell_format)
            worksheet.write(row, 1, count, cell_format)

class ApplicationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = JobApplication
    template_name = 'jobs/application_list.html'
    context_object_name = 'applications'
    paginate_by = 10
    
    def test_func(self):
        return hasattr(self.request.user, 'myapp_jobseeker')
    
    def get_queryset(self):
        return JobApplication.objects.filter(
            applicant=self.request.user.myapp_jobseeker
        ).select_related(
            'job',
            'job__company'
        ).order_by('-applied_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Applications'
        return context

class EmployerAnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'jobs/employer_analytics_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employer = self.request.user.myapp_employer
        
        # Get date range from request
        date_range = self.request.GET.get('date_range', '30')  # Default to 30 days
        days = int(date_range)
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get all jobs for this employer's company
        jobs = JobPosting.objects.filter(company=employer.company)
        
        # Calculate key metrics
        context.update({
            'active_jobs_count': jobs.filter(is_active=True).count(),
            'total_views': jobs.aggregate(total=Sum('metrics__views'))['total'] or 0,
            'total_applications': JobApplication.objects.filter(job__in=jobs).count(),
            'avg_ctr': self._calculate_ctr(jobs),
            
            # Get top performing jobs
            'top_jobs': self._get_top_performing_jobs(jobs),
            
            # Get application trends
            'application_trends': self._get_application_trends(jobs, start_date),
            
            # Get experience distribution
            'experience_distribution': self._get_experience_distribution(jobs),
            
            # Current date range
            'date_range': date_range
        })
        
        return context
    
    def _calculate_ctr(self, jobs):
        """Calculate the average Click-Through Rate across all jobs"""
        total_views = jobs.aggregate(total=Sum('metrics__views'))['total'] or 0
        total_applications = JobApplication.objects.filter(job__in=jobs).count()
        return (total_applications / total_views * 100) if total_views > 0 else 0
    
    def _get_top_performing_jobs(self, jobs, limit=5):
        """Get the top performing jobs based on application rate"""
        return jobs.annotate(
            application_count=Count('applications'),
            application_rate=Case(
                When(metrics__views__gt=0,
                     then=F('application_count') * 100.0 / F('metrics__views')),
                default=0,
                output_field=FloatField(),
            )
        ).order_by('-application_rate')[:limit]
    
    def _get_application_trends(self, jobs, start_date):
        """Get daily application trends"""
        return JobApplication.objects.filter(
            job__in=jobs,
            applied_at__gte=start_date
        ).annotate(
            date=TruncDate('applied_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
    
    def _get_experience_distribution(self, jobs):
        """Get distribution of applicant experience levels"""
        return JobApplication.objects.filter(
            job__in=jobs
        ).values(
            'applicant__experience_years'
        ).annotate(
            count=Count('id')
        ).order_by('applicant__experience_years')

class ApplicationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = JobApplication
    template_name = 'jobs/application_confirm_delete.html'
    success_url = reverse_lazy('jobs:application_list')
    
    def test_func(self):
        application = self.get_object()
        return application.applicant.user == self.request.user
    
    def delete(self, request, *args, **kwargs):
        application = self.get_object()
        messages.success(request, f'Application for {application.job.title} has been successfully deleted.')
        return super().delete(request, *args, **kwargs)

class SavedJobDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = SavedJob
    template_name = 'jobs/saved_job_detail.html'
    context_object_name = 'saved_job'
    
    def test_func(self):
        saved_job = self.get_object()
        return saved_job.job_seeker.user == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['job'] = self.object.job
        return context

class SavedJobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = SavedJob
    template_name = 'jobs/saved_job_confirm_delete.html'
    success_url = reverse_lazy('jobs:saved_job_list')
    
    def test_func(self):
        saved_job = self.get_object()
        return saved_job.job_seeker.user == self.request.user
    
    def delete(self, request, *args, **kwargs):
        saved_job = self.get_object()
        messages.success(request, f'Job "{saved_job.job.title}" has been removed from your saved jobs.')
        return super().delete(request, *args, **kwargs)

class JobAlertDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = JobAlert
    template_name = 'jobs/job_alert_detail.html'
    context_object_name = 'alert'
    
    def test_func(self):
        alert = self.get_object()
        return alert.job_seeker.user == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get matching jobs for this alert
        context['matching_jobs'] = JobPosting.objects.filter(
            is_active=True,
            title__icontains=alert.keywords,
            location__icontains=alert.location,
            job_type__in=alert.job_types.split(',') if alert.job_types else []
        ).select_related('company')[:10]
        
        # Get alert history
        context['alert_history'] = self.object.history.all().order_by('-created_at')[:5]
        
        return context

class NotificationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Notification
    template_name = 'jobs/notification_detail.html'
    context_object_name = 'notification'
    
    def test_func(self):
        notification = self.get_object()
        return notification.user == self.request.user
    
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Mark notification as read when viewed
        if not self.object.is_read:
            self.object.is_read = True
            self.object.read_at = timezone.now()
            self.object.save()
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related content based on notification type
        if self.object.content_type.model == 'jobapplication':
            context['application'] = self.object.content_object
        elif self.object.content_type.model == 'jobposting':
            context['job'] = self.object.content_object
        
        return context

class NotificationUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Notification
    template_name = 'jobs/notification_form.html'
    fields = ['is_read']
    success_url = reverse_lazy('jobs:notification_list')
    
    def test_func(self):
        notification = self.get_object()
        return notification.user == self.request.user
    
    def form_valid(self, form):
        if form.cleaned_data['is_read'] and not self.object.is_read:
            form.instance.read_at = timezone.now()
        elif not form.cleaned_data['is_read'] and self.object.is_read:
            form.instance.read_at = None
        return super().form_valid(form)

class NotificationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Notification
    template_name = 'jobs/notification_confirm_delete.html'
    success_url = reverse_lazy('jobs:notification_list')
    
    def test_func(self):
        notification = self.get_object()
        return notification.user == self.request.user
    
    def delete(self, request, *args, **kwargs):
        notification = self.get_object()
        messages.success(request, f'Notification "{notification.title}" has been successfully deleted.')
        return super().delete(request, *args, **kwargs)

class RoleSelectionView(TemplateView):
    template_name = 'jobs/role_selection.html'

    def get(self, request, *args, **kwargs):
        # If user is authenticated and has a role, redirect to dashboard
        if request.user.is_authenticated:
            if hasattr(request.user, 'myapp_employer'):
                return redirect('jobs:employer_dashboard')
            elif hasattr(request.user, 'myapp_jobseeker'):
                return redirect('jobs:jobseeker_dashboard')
        # Otherwise, show the role selection page (public)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_authenticated'] = self.request.user.is_authenticated
        return context

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'jobs/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return self.request.user.notifications.filter(is_read=False).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.request.user.notifications.filter(is_read=False).count()
        return context

class NotificationSettingsView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'jobs/notification_settings.html'
    fields = []
    success_url = reverse_lazy('jobs:notification_settings')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get notification preferences
        if hasattr(user, 'myapp_jobseeker'):
            context.update({
                'email_preferences': {
                    'application_status': user.myapp_jobseeker.notify_application_status,
                    'job_alerts': user.myapp_jobseeker.notify_job_alerts,
                    'saved_searches': user.myapp_jobseeker.notify_saved_searches,
                    'messages': user.myapp_jobseeker.notify_messages
                }
            })
        elif hasattr(user, 'myapp_employer'):
            context.update({
                'email_preferences': {
                    'new_applications': user.myapp_employer.notify_new_applications,
                    'messages': user.myapp_employer.notify_messages
                }
            })
        
        return context

    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.POST
        
        if hasattr(user, 'myapp_jobseeker'):
            user.myapp_jobseeker.notify_application_status = data.get('notify_application_status') == 'on'
            user.myapp_jobseeker.notify_job_alerts = data.get('notify_job_alerts') == 'on'
            user.myapp_jobseeker.notify_saved_searches = data.get('notify_saved_searches') == 'on'
            user.myapp_jobseeker.notify_messages = data.get('notify_messages') == 'on'
            user.myapp_jobseeker.save()
        elif hasattr(user, 'myapp_employer'):
            user.myapp_employer.notify_new_applications = data.get('notify_new_applications') == 'on'
            user.myapp_employer.notify_messages = data.get('notify_messages') == 'on'
            user.myapp_employer.save()
        
        messages.success(request, 'Notification preferences updated successfully.')
        return redirect('jobs:notification_settings')

class EmployerJobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = JobPosting
    template_name = 'jobs/jobposting_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def test_func(self):
        return hasattr(self.request.user, 'myapp_employer')

    def get_queryset(self):
        return JobPosting.objects.filter(
            company=self.request.user.myapp_employer.company
        ).annotate(
            total_applications=Count('applications')
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_jobs'] = self.get_queryset().filter(is_active=True).count()
        context['total_jobs'] = self.get_queryset().count()
        return context

class JobSeekerProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = JobSeeker
    form_class = JobSeekerProfileForm
    template_name = 'jobs/jobseeker_profile_form.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')

    def test_func(self):
        return hasattr(self.request.user, 'myapp_jobseeker')

    def get_object(self, queryset=None):
        return self.request.user.myapp_jobseeker

    def form_valid(self, form):
        messages.success(self.request, 'Your profile has been updated successfully.')
        return super().form_valid(form)

@method_decorator(require_GET, name='dispatch')
class JobAjaxSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        location = request.GET.get('location', '')
        job_type = request.GET.get('job_type', '')
        jobs = JobPosting.objects.filter(is_active=True)
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query)
            )
        if location:
            jobs = jobs.filter(location__icontains=location)
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        jobs = jobs.order_by('-created_at')[:20]

        results = [{
            'id': job.id,
            'title': job.title,
            'company': job.company.name,
            'location': job.location,
            'job_type': job.get_job_type_display(),
            'detail_url': reverse('jobs:job_detail', args=[job.id])
        } for job in jobs]
        return JsonResponse({'results': results})

class JobSearchResultsView(ListView):
    model = JobPosting
    template_name = 'jobs/job_search_results.html'
    context_object_name = 'jobs'
    paginate_by = 20

    def get_queryset(self):
        queryset = JobPosting.objects.filter(is_active=True)
        query = self.request.GET.get('q')
        location = self.request.GET.get('location')
        job_type = self.request.GET.get('job_type')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query)
            )
        if location:
            queryset = queryset.filter(location__icontains=location)
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        return queryset.order_by('-created_at')

class ApplicationStatusActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        # Only employers can change status
        return hasattr(self.request.user, 'myapp_employer')

    @method_decorator(require_POST)
    def post(self, request, application_id):
        application = get_object_or_404(JobApplication, pk=application_id)
        new_status = request.POST.get('status')
        if new_status not in dict(JobApplication.STATUS_CHOICES):
            return JsonResponse({'error': 'Invalid status'}, status=400)
        application.status = new_status
        application.save()
        return redirect('jobs:application_detail', pk=application_id)
