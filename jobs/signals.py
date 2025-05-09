from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from myapp.models import JobSeeker, Employer, Company

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_staff:
            # Create a default company for the employer
            company = Company.objects.create(
                name=f"{instance.username}'s Company",
                description='Default company description',
                location='Default location',
                industry='Default industry'
            )
            # Create an employer profile
            Employer.objects.create(
                user=instance,
                company=company,
                job_title='',
                department='',
                phone='',
                is_primary_contact=False,
                can_post_jobs=True
            )
        else:
            # Create a job seeker profile
            JobSeeker.objects.create(
                user=instance,
                bio='',
                experience_level='entry',
                location='',
                is_available=True
            )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if instance.is_staff:
        if hasattr(instance, 'myapp_employer'):
            instance.myapp_employer.save()
    else:
        if hasattr(instance, 'myapp_jobseeker'):
            instance.myapp_jobseeker.save()