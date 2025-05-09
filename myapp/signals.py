from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import JobApplication, JobAlert, JobPosting, JobViewLog

@receiver(post_save, sender=JobApplication)
def application_status_changed(sender, instance, created, **kwargs):
    """Send email notifications when application status changes"""
    if not created and instance.status != instance._original_status:
        # Send email to applicant
        subject = f'Application Status Update - {instance.job.title}'
        message = f'Your application for {instance.job.title} has been updated to {instance.get_status_display()}'
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.applicant.user.email],
            fail_silently=True,
        )

        # Send email to employer
        if instance.status == 'accepted':
            subject = f'Application Accepted - {instance.job.title}'
            message = f'You have accepted the application from {instance.applicant.user.get_full_name()}'
            employer_emails = [employer.user.email for employer in instance.job.company.employers.all()]
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                employer_emails,
                fail_silently=True,
            )

@receiver(post_save, sender=JobPosting)
def job_posted(sender, instance, created, **kwargs):
    """Send job alerts when new job is posted"""
    if created:
        # Build filter conditions dynamically
        filter_conditions = {'is_active': True}
        
        if instance.title:
            filter_conditions['keywords__icontains'] = instance.title
            
        if instance.job_type:
            filter_conditions['job_type'] = instance.job_type
            
        if instance.category:
            filter_conditions['category'] = instance.category
            
        if instance.location:
            filter_conditions['location__icontains'] = instance.location
            
        if instance.salary_max:
            filter_conditions['min_salary__lte'] = instance.salary_max

        # Find matching job alerts
        matching_alerts = JobAlert.objects.filter(**filter_conditions)

        # Send email notifications
        for alert in matching_alerts:
            subject = f'New Job Match - {instance.title}'
            message = f'''
            A new job matching your alert criteria has been posted:
            
            Title: {instance.title}
            Company: {instance.company.name}
            Location: {instance.location or 'Not specified'}
            Salary Range: {f"${instance.salary_min:,.2f} - ${instance.salary_max:,.2f}" if instance.salary_min and instance.salary_max else 'Not specified'}
            
            View the full job posting here: {instance.get_absolute_url()}
            '''
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [alert.job_seeker.user.email],
                fail_silently=True,
            )
            
            # Update last sent timestamp
            alert.last_sent = timezone.now()
            alert.save()

@receiver(post_save, sender=JobViewLog)
def update_job_metrics(sender, instance, created, **kwargs):
    """Update job metrics when viewed"""
    if created:
        instance.job.update_metrics()

@receiver(post_save, sender=JobApplication)
def update_job_metrics_on_application(sender, instance, created, **kwargs):
    """Update job metrics when application is created"""
    if created:
        instance.job.update_metrics() 