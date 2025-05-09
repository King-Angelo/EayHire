from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from myapp.models import Employer, JobSeeker

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        user = request.user
        print("Login redirect for user:", user.email)

        if user.is_staff:
            print("User is staff, redirecting to admin")
            return reverse('admin:index')

        # Check if user has an employer profile
        if Employer.objects.filter(user=user).exists():
            print("User has employer profile, redirecting to employer dashboard")
            return reverse('jobs:employer_dashboard')

        # Check if user has a jobseeker profile
        elif JobSeeker.objects.filter(user=user).exists():
            print("User has jobseeker profile, redirecting to jobseeker dashboard")
            return reverse('jobs:jobseeker_dashboard')

        print("No role found, redirecting to role selection")
        return reverse('jobs:role_selection')
