from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import JobSeeker, Employer, JobApplication, JobPosting, Notification
from django.db.models import Q

class EmailVerificationRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow admin URLs
        if request.path_info.startswith('/admin'):
            return self.get_response(request)

        # Debug print
        print("[DEBUG] Processing path:", request.path_info)
            
        # Public paths that don't require authentication
        public_paths = [
            'account_login',
            'account_signup',
            'account_reset_password',
            'account_reset_password_done',
            'account_reset_password_from_key',
            'account_reset_password_from_key_done',
            'account_logout',
            'account_email_verification_sent',
            'account_confirm_email',
            'account_email',
            'jobs:home',
            'home',
            'jobs:job_list',
            'job_list',
            'jobs:job_detail',
            'jobs:role_selection',
            'jobs:employer_register',
            'jobs:jobseeker_register',
            'myapp:employer_register',
            'myapp:jobseeker_register',
            'test_public',
            'privacy_policy',
            'terms',
            'contact',
        ]
        
        # Check if the current path is public
        is_public = False
        
        # First check if the path matches any known public paths
        public_path_patterns = [
            '/jobs/role-selection/',
            '/jobs/employer/register/',
            '/jobs/jobseeker/register/',
            '/employer/register/',
            '/jobseeker/register/',
            '/accounts/login/',
            '/accounts/signup/',
            '/accounts/password/reset/',
            '/accounts/confirm-email/',
            '/accounts/email/',
            '/accounts/logout/',
        ]
        
        # Make path matching more flexible (allow with or without trailing slash)
        if any(request.path_info.rstrip('/') == pattern.rstrip('/') for pattern in public_path_patterns):
            print("[DEBUG] Path matches public pattern:", request.path_info)
            is_public = True
        else:
            try:
                view_name = resolve(request.path_info).url_name
                print("[DEBUG] Resolved view name:", view_name, "for path:", request.path_info)
                is_public = view_name in public_paths
                if is_public:
                    print("[DEBUG] View name is in public paths")
            except Exception as e:
                print("[DEBUG] Middleware resolve error:", e, "for path:", request.path_info)
                is_public = False

        print("[DEBUG] Is public path:", is_public)

        # Check if session is valid
        if request.user.is_authenticated:
            # Ensure session is working
            request.session.set_test_cookie()
            if not request.session.test_cookie_worked():
                # If session isn't working, clear session and redirect to login
                request.session.flush()
                messages.error(request, _('Please enable cookies and try again.'))
                return redirect('account_login')
            request.session.delete_test_cookie()

            # If user is authenticated but email not verified
            if not request.user.emailaddress_set.filter(verified=True).exists() and not is_public:
                # Only redirect if not already on verification pages
                if not request.path.startswith(reverse('account_email_verification_sent')):
                    messages.warning(
                        request,
                        _('Please verify your email address to access this page. '
                          'Check your inbox for the verification email.')
                    )
                    return redirect('account_email_verification_sent')
        elif not is_public:
            # If user is not authenticated and trying to access protected page
            messages.warning(request, _('Please log in to access this page.'))
            return redirect('account_login')

        response = self.get_response(request)
        print(f"[MIDDLEWARE] Response type: {type(response)}, status: {getattr(response, 'status_code', 'N/A')}")
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Get the view name
        try:
            view_name = resolve(request.path_info).url_name
        except:
            view_name = ''

        # Redirect employers from general jobs page to their dashboard
        if request.user.is_authenticated and hasattr(request.user, 'myapp_employer'):
            if request.path_info == '/jobs/' or view_name == 'jobs:home':
                return redirect('jobs:employer_dashboard')

        # Redirect jobseekers from general jobs page to their dashboard
        if request.user.is_authenticated and hasattr(request.user, 'myapp_jobseeker'):
            if request.path_info == '/jobs/' or view_name == 'jobs:home':
                return redirect('jobs:jobseeker_dashboard')

        # If user is trying to access role-specific pages
        if view_name in ['employer_dashboard', 'jobseeker_dashboard']:
            if not request.user.is_authenticated:
                messages.warning(request, _('Please log in to access this page.'))
                return redirect('account_login')
            
            if not request.user.emailaddress_set.filter(verified=True).exists():
                messages.warning(
                    request,
                    _('Please verify your email address to access the dashboard.')
                )
                return redirect('account_email_verification_sent')

            # Check if user has the correct role for the page
            if view_name == 'employer_dashboard':
                if not hasattr(request.user, 'myapp_employer'):
                    messages.error(request, _('You need to register as an employer to access this page.'))
                    return redirect('jobs:role_selection')
                elif not request.user.myapp_employer.can_post_jobs:
                    messages.warning(request, _('Your employer account is pending approval.'))
                    return redirect('jobs:home')
            elif view_name == 'jobseeker_dashboard' and not hasattr(request.user, 'myapp_jobseeker'):
                messages.error(request, _('You need to register as a job seeker to access this page.'))
                return redirect('jobs:role_selection')

        return None

class UserProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user has a profile
            has_jobseeker = hasattr(request.user, 'myapp_jobseeker')
            has_employer = hasattr(request.user, 'myapp_employer')
            
            # If user has no profile and is not on registration or role selection page
            if not (has_jobseeker or has_employer):
                current_path = request.path_info
                if not any(path in current_path for path in ['/register/', '/role-selection/', '/accounts/']):
                    messages.info(request, 'Please complete your profile registration.')
                    return redirect('jobs:role_selection')
        
        response = self.get_response(request)
        return response

class NotificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Get unread notifications count
            request.unread_notifications_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
            
            # Get recent notifications
            request.recent_notifications = Notification.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
        
        response = self.get_response(request)
        return response

class JobApplicationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'myapp_jobseeker'):
            # Get pending applications count
            request.pending_applications_count = JobApplication.objects.filter(
                applicant=request.user.myapp_jobseeker,
                status='pending'
            ).count()
            
            # Get recent applications
            request.recent_applications = JobApplication.objects.filter(
                applicant=request.user.myapp_jobseeker
            ).order_by('-applied_at')[:5]
        
        response = self.get_response(request)
        return response

class JobPostingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'myapp_employer'):
            # Get active job postings count
            request.active_jobs_count = JobPosting.objects.filter(
                company=request.user.myapp_employer.company,
                is_active=True
            ).count()
            
            # Get recent job postings
            request.recent_jobs = JobPosting.objects.filter(
                company=request.user.myapp_employer.company
            ).order_by('-created_at')[:5]
        
        response = self.get_response(request)
        return response 