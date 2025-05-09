from django.core.management.base import BaseCommand
from myapp.models import JobPosting
from django.utils import timezone
from django.db.models import F
from django.db import transaction

class Command(BaseCommand):
    help = 'Deactivates expired job postings and sends notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options['dry_run']

        # Get all active jobs that have expired
        expired_jobs = JobPosting.objects.filter(
            is_active=True,
            deadline__lt=now
        ).select_related('employer')

        if dry_run:
            self.stdout.write(f"Found {expired_jobs.count()} expired jobs that would be deactivated:")
            for job in expired_jobs:
                self.stdout.write(f"- {job.title} (ID: {job.id}) posted by {job.employer.company_name}")
            return

        with transaction.atomic():
            # Deactivate expired jobs
            count = expired_jobs.update(is_active=False)

            # Log the deactivated jobs
            for job in expired_jobs:
                self.stdout.write(
                    self.style.WARNING(
                        f"Deactivated job: {job.title} (ID: {job.id}) posted by {job.employer.company_name}"
                    )
                )

                # Send notification to employer (you can implement this based on your notification system)
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    subject = f"Job Posting Expired: {job.title}"
                    message = f"""
                    Dear {job.employer.company_name},

                    Your job posting "{job.title}" has expired and has been automatically deactivated.
                    The job was posted on {job.created_at.strftime('%B %d, %Y')} and expired on {job.deadline.strftime('%B %d, %Y at %I:%M %p')}.

                    If you would like to repost this job or create a new posting, please visit your employer dashboard.

                    Best regards,
                    The Job Portal Team
                    """
                    
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [job.employer.user.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to send notification email for job {job.id}: {str(e)}"
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Successfully deactivated {count} expired job postings")
        ) 