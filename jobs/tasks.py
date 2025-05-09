from celery import shared_task
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from myapp.models import JobPosting
from django.db.models import F
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import SavedSearch

@shared_task
def deactivate_expired_jobs():
    """
    Task to deactivate expired job postings and send notifications.
    """
    call_command('deactivate_expired_jobs')

@shared_task
def send_deadline_reminders():
    """
    Task to send reminder emails for jobs approaching their deadline.
    """
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    three_days = now + timedelta(days=3)
    week = now + timedelta(days=7)

    # Get jobs with deadlines in the next day, 3 days, and week
    approaching_deadlines = {
        'day': JobPosting.objects.filter(
            is_active=True,
            deadline__gt=now,
            deadline__lte=tomorrow
        ).select_related('employer'),
        'three_days': JobPosting.objects.filter(
            is_active=True,
            deadline__gt=tomorrow,
            deadline__lte=three_days
        ).select_related('employer'),
        'week': JobPosting.objects.filter(
            is_active=True,
            deadline__gt=three_days,
            deadline__lte=week
        ).select_related('employer')
    }

    for period, jobs in approaching_deadlines.items():
        for job in jobs:
            try:
                # Prepare email context
                context = {
                    'job': job,
                    'company_name': job.employer.company_name,
                    'deadline': job.deadline,
                    'period': period,
                    'applications_count': job.applications_count,
                }

                # Render email content from template
                subject = f"Job Posting Deadline Approaching: {job.title}"
                html_message = render_to_string('jobs/emails/deadline_reminder.html', context)
                plain_message = render_to_string('jobs/emails/deadline_reminder.txt', context)

                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[job.employer.user.email],
                    html_message=html_message,
                    fail_silently=True
                )
            except Exception as e:
                print(f"Failed to send reminder email for job {job.id}: {str(e)}")

@shared_task
def update_job_metrics():
    """
    Task to update job metrics like views count and applications count.
    """
    # Update metrics that need periodic calculation
    jobs = JobPosting.objects.filter(is_active=True)
    
    for job in jobs:
        # Update applications count
        job.applications_count = job.application_set.count()
        
        # Calculate application rate (applications per view)
        if job.views_count > 0:
            application_rate = (job.applications_count / job.views_count) * 100
        else:
            application_rate = 0
            
        # Update job metrics
        JobPosting.objects.filter(id=job.id).update(
            applications_count=job.applications_count,
            application_rate=application_rate
        )

@shared_task
def send_saved_search_notifications():
    """
    Send email notifications for saved searches that have new matching jobs
    """
    searches = SavedSearch.objects.filter(email_notifications=True)
    
    for search in searches:
        new_jobs = search.get_new_matches_since_last_notification()
        
        if new_jobs.exists():
            # Prepare email content
            context = {
                'jobseeker': search.jobseeker,
                'search_title': search.title,
                'new_jobs': new_jobs,
                'search_url': f'/jobs/?{search.search_params}'
            }
            
            html_message = render_to_string('jobs/emails/new_jobs_notification.html', context)
            plain_message = render_to_string('jobs/emails/new_jobs_notification.txt', context)
            
            # Send email
            send_mail(
                subject=f'New jobs matching your saved search: {search.title}',
                message=plain_message,
                html_message=html_message,
                from_email='noreply@jobportal.com',
                recipient_list=[search.jobseeker.user.email],
                fail_silently=True
            )
            
            # Update last notification timestamp
            search.last_notification_sent = timezone.now()
            search.save()

@shared_task
def update_job_matches():
    """
    Task to update job matches for all active jobs and job seekers
    """
    from .models import JobPosting, JobSeeker, JobMatch
    
    # Get all active jobs and job seekers
    active_jobs = JobPosting.objects.filter(is_active=True)
    job_seekers = JobSeeker.objects.filter(user__is_active=True)
    
    for job in active_jobs:
        for seeker in job_seekers:
            # Skip if the job seeker has already applied
            if job.applications.filter(applicant=seeker).exists():
                continue
                
            # Get or create job match
            match, created = JobMatch.objects.get_or_create(
                job=job,
                jobseeker=seeker,
                defaults={
                    'match_score': 0,
                    'skill_match': 0,
                    'experience_match': 0,
                    'salary_match': 0,
                    'location_match': 0
                }
            )
            
            # Calculate and update match score
            match.calculate_match_score()
            match.save()
            
            # Send notification if it's a high match (over 80%)
            if match.match_score >= 80 and created:
                from .models import Notification
                Notification.objects.create(
                    user=seeker.user,
                    notification_type='job_match',
                    title=f'High Match: {job.title}',
                    message=f'We found a job that matches {match.match_score:.0f}% of your profile!',
                    target_url=f'/jobs/{job.id}/',
                    data={
                        'job_id': job.id,
                        'match_score': float(match.match_score),
                        'skill_match': float(match.skill_match),
                        'experience_match': float(match.experience_match),
                        'salary_match': float(match.salary_match),
                        'location_match': float(match.location_match)
                    }
                ) 