import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from jobs.models import JobSeeker, Employer

def create_profiles():
    # Get all users
    users = User.objects.all()
    
    for user in users:
        print(f"\nProcessing user: {user.username}")
        
        # Create JobSeeker profile if it doesn't exist
        if not hasattr(user, 'jobseeker'):
            try:
                JobSeeker.objects.create(
                    user=user,
                    phone='',
                    address='',
                    education='',
                    experience='',
                    skills=''
                )
                print(f"Created JobSeeker profile for {user.username}")
            except Exception as e:
                print(f"Error creating JobSeeker profile: {e}")
        
        # Create Employer profile if it doesn't exist
        if not hasattr(user, 'employer'):
            try:
                Employer.objects.create(
                    user=user,
                    company_name=f"{user.username}'s Company",
                    company_description='',
                    industry='',
                    company_size='',
                    location='',
                    website=''
                )
                print(f"Created Employer profile for {user.username}")
            except Exception as e:
                print(f"Error creating Employer profile: {e}")

if __name__ == '__main__':
    create_profiles() 