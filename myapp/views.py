from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, TemplateView, UpdateView
from django.contrib.auth import login
from django.urls import reverse_lazy
from .models import Employer, JobSeeker, JobPosting, JobApplication, Notification
from .forms import EmployerRegistrationForm, JobSeekerRegistrationForm, JobPostingForm, JobApplicationForm, JobSeekerProfileForm, ContactForm, EmployerProfileForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, HttpResponseRedirect
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django import forms

def index(request):
    return render(request, 'index.html')

def home(request):
    return render(request, 'home.html')

class EmployerRegistrationView(CreateView):
    model = Employer
    form_class = EmployerRegistrationForm
    template_name = 'jobs/employer_registration.html'
    success_url = reverse_lazy('jobs:employer_dashboard')

    def get(self, request, *args, **kwargs):
        print("[DEBUG] EmployerRegistrationView.get called")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("[DEBUG] EmployerRegistrationView.post called")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        print("[DEBUG] EmployerRegistrationView.form_valid called")
        email = form.cleaned_data.get('email')
        print("[DEBUG] Email:", email)
        
        # Prevent duplicate employer or jobseeker for the same email
        if Employer.objects.filter(user__email=email).exists():
            form.add_error(None, 'An employer account with this email already exists.')
            return self.form_invalid(form)
            
        # Remove jobseeker profile if exists, but do NOT delete the user
        JobSeeker.objects.filter(user__email=email).delete()
        
        response = super().form_valid(form)
        user = self.object  # FIX: self.object is the User instance
        
        if not self.request.user.is_authenticated:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            
        # Ensure email confirmation is sent
        if not EmailAddress.objects.filter(user=user, email=user.email).exists():
            send_email_confirmation(self.request, user)
            
        print("SUCCESS MESSAGE SET")
        messages.success(self.request, 'Employer account created successfully! Please check your email to verify your account.')
        return response

    def form_invalid(self, form):
        print("[DEBUG] EmployerRegistrationView.form_invalid called")
        print("[DEBUG] Form errors:", form.errors)
        return super().form_invalid(form)

class JobSeekerRegistrationView(CreateView):
    model = JobSeeker
    form_class = JobSeekerRegistrationForm
    template_name = 'jobs/jobseeker_registration.html'
    success_url = reverse_lazy('jobs:jobseeker_dashboard')

    def get(self, request, *args, **kwargs):
        print("[DEBUG] JobSeekerRegistrationView.get called")
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("[DEBUG] JobSeekerRegistrationView.post called")
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        print("[DEBUG] JobSeekerRegistrationView.form_valid called")
        email = form.cleaned_data.get('email')
        print("[DEBUG] Email:", email)
        
        # Prevent duplicate jobseeker or employer for the same email
        if JobSeeker.objects.filter(user__email=email).exists():
            form.add_error(None, 'A jobseeker account with this email already exists.')
            return self.form_invalid(form)
            
        # Remove employer profile if exists, but do NOT delete the user
        Employer.objects.filter(user__email=email).delete()
        
        # Save the user first
        user = form.save()
        
        if not self.request.user.is_authenticated:
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            
        # Ensure email confirmation is sent
        if not EmailAddress.objects.filter(user=user, email=user.email).exists():
            send_email_confirmation(self.request, user)
            
        messages.success(self.request, 'Job seeker account created successfully! Please check your email to verify your account.')
        return super().form_valid(form)

    def form_invalid(self, form):
        print("[DEBUG] JobSeekerRegistrationView.form_invalid called")
        print("[DEBUG] Form errors:", form.errors)
        return super().form_invalid(form)

class JobListView(ListView):
    model = JobPosting
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        queryset = JobPosting.objects.filter(is_active=True)
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__name=category)
        return queryset

class JobDetailView(DetailView):
    model = JobPosting
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['has_applied'] = JobApplication.objects.filter(
                job=self.object,
                applicant__user=self.request.user
            ).exists()
        return context

class JobApplicationView(LoginRequiredMixin, CreateView):
    model = JobApplication
    form_class = JobApplicationForm
    template_name = 'jobs/apply_job.html'

    def get_success_url(self):
        return reverse_lazy('job_detail', args=[self.kwargs['pk']])

    def form_valid(self, form):
        job = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        if JobApplication.objects.filter(job=job, applicant__user=self.request.user).exists():
            messages.error(self.request, 'You have already applied for this job.')
            return redirect('job_detail', pk=job.pk)
        
        form.instance.job = job
        form.instance.applicant = self.request.user.jobseeker
        form.instance.status = 'pending'
        messages.success(self.request, 'Your application has been submitted successfully.')
        return super().form_valid(form)

class EmployerDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'jobs/employer_dashboard.html'
    
    def test_func(self):
        # Debug prints
        print("User:", self.request.user.email)
        print("Has employer profile:", Employer.objects.filter(user=self.request.user).exists())
        print("Has jobseeker profile:", JobSeeker.objects.filter(user=self.request.user).exists())
        return Employer.objects.filter(user=self.request.user).exists()

class JobseekerProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        jobseeker = get_object_or_404(JobSeeker, user=request.user)
        form = JobSeekerProfileForm(instance=jobseeker)  # Use your form here
        return render(request, 'jobseeker/profile_edit.html', {'form': form})

    def post(self, request):
        jobseeker = get_object_or_404(JobSeeker, user=request.user)
        form = JobSeekerProfileForm(request.POST, instance=jobseeker)  # Use your form here
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('jobseeker_profile_edit')  # Redirect to the same page or another page
        return render(request, 'jobseeker/profile_edit.html', {'form': form})
    
    def jobseeker_registration(request):
        return render(request, 'accounts/jobseeker_registration.html')

def employer_jobs(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'employer'):
        return redirect('home')
    jobs = JobPosting.objects.filter(employer=request.user.employer)
    return render(request, 'employer/jobs.html', {'jobs': jobs})

class JobPostingCreateView(CreateView):
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'employer/job_create.html'
    success_url = reverse_lazy('jobs:employer_jobs')

    def form_valid(self, form):
        # Set the employer to the current user
        form.instance.employer = self.request.user.employer
        return super().form_valid(form)

class JobPostingUpdateView(UpdateView):
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'employer/job_edit.html'
    success_url = reverse_lazy('jobs:employer_jobs')

    def get_queryset(self):
        # Only allow editing jobs for the current employer
        return JobPosting.objects.filter(employer=self.request.user.employer)

class SimpleContactForm(forms.Form):
    recipient_email = forms.EmailField(label='Recipient (Employer) Email')
    name = forms.CharField(max_length=100)
    email = forms.EmailField(label='Your Email')
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)

def contact_new(request):
    from myapp.models import Employer, JobSeeker, Notification
    from django.contrib import messages
    if request.method == 'POST':
        form = SimpleContactForm(request.POST)
        if form.is_valid():
            recipient_email = form.cleaned_data['recipient_email']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message_body = form.cleaned_data['message']
            recipient_user = None
            recipient_role = None
            # Determine sender's role and look up recipient accordingly
            if request.user.is_authenticated and hasattr(request.user, 'myapp_employer'):
                # Sender is employer, recipient should be jobseeker
                try:
                    jobseeker = JobSeeker.objects.get(user__email=recipient_email)
                    recipient_user = jobseeker.user
                    recipient_role = 'jobseeker'
                except JobSeeker.DoesNotExist:
                    form.add_error('recipient_email', 'No jobseeker found with this email.')
                    return render(request, 'jobs/contact_new.html', {'form': form})
            elif request.user.is_authenticated and hasattr(request.user, 'myapp_jobseeker'):
                # Sender is jobseeker, recipient should be employer
                try:
                    employer = Employer.objects.get(user__email=recipient_email)
                    recipient_user = employer.user
                    recipient_role = 'employer'
                except Employer.DoesNotExist:
                    form.add_error('recipient_email', 'No employer found with this email.')
                    return render(request, 'jobs/contact_new.html', {'form': form})
            else:
                form.add_error('recipient_email', 'You must be logged in as an employer or jobseeker to send a message.')
                return render(request, 'jobs/contact_new.html', {'form': form})
            # Notify the recipient
            Notification.objects.create(
                user=recipient_user,
                notification_type='message',
                title=f"Contact from {name}",
                message=f"Subject: {subject}\n\nMessage: {message_body}\n\nSender Email: {email}",
            )
            # Notify the sender
            Notification.objects.create(
                user=request.user,
                notification_type='message',
                title=f"Message sent to {recipient_email}",
                message=f"Your message to {recipient_email} was sent successfully.",
            )
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect('/contact/')
    else:
        form = SimpleContactForm()
    return render(request, 'jobs/contact_new.html', {'form': form})

def contact(request):
    print(f"[CONTACT VIEW] Method: {request.method}, Path: {request.path}")
    print(f"[CONTACT VIEW] Session Key: {request.session.session_key}")
    print(f"[CONTACT VIEW] Message Storage Backend: {request._messages.__class__}")
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            employer = form.cleaned_data['employer']
            # Notify all employer users for the company
            for employer_user in employer.company.employers.all():
                Notification.objects.create(
                    user=employer_user.user,
                    notification_type='message',
                    title=f"Contact from {form.cleaned_data['name']}",
                    message=f"Subject: {form.cleaned_data['subject']}\n\nMessage: {form.cleaned_data['message']}\n\nEmail: {form.cleaned_data['email']}",
                )
            # Notify the jobseeker (sender) if authenticated and is a jobseeker
            if request.user.is_authenticated and hasattr(request.user, 'jobseeker'):
                Notification.objects.create(
                    user=request.user,
                    notification_type='message',
                    title=f"Message sent to {employer.user.get_full_name()}",
                    message=f"Your message to {employer.user.get_full_name()} was sent successfully.",
                )
            print("SUCCESS MESSAGE SET")
            messages.success(request, 'Thank you for your message. We will get back to you soon!')
            return HttpResponseRedirect('/contact/')
    else:
        form = ContactForm()
    # Print all messages in the request before rendering
    print(f"[CONTACT VIEW] Messages in request before render: {[str(m) for m in messages.get_messages(request)]}")
    return render(request, 'jobs/contact.html', {'form': form})

def employer_search(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'myapp_employer'):
        return redirect('home')
    query = request.GET.get('q', '').strip()
    your_jobs = []
    other_jobs = []
    applicants = []
    if query:
        # Your active jobs (search title only)
        your_jobs = JobPosting.objects.filter(
            company=request.user.myapp_employer.company,
            is_active=True,
            title__icontains=query
        )
        # Other active jobs (search title only)
        other_jobs = JobPosting.objects.filter(
            is_active=True,
            title__icontains=query
        ).exclude(company=request.user.myapp_employer.company)
        # Search applicants (JobSeekers) by name or email
        applicants = JobSeeker.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query)
        )
    else:
        # Show all your active jobs if no query
        your_jobs = JobPosting.objects.filter(
            company=request.user.myapp_employer.company,
            is_active=True
        )
        other_jobs = JobPosting.objects.filter(
            is_active=True
        ).exclude(company=request.user.myapp_employer.company)
    return render(request, 'employer/employer_search_results.html', {
        'query': query,
        'your_jobs': your_jobs,
        'other_jobs': other_jobs,
        'applicants': applicants,
    })

@login_required
def employer_profile(request):
    employer = get_object_or_404(Employer, user=request.user)
    
    if request.method == 'POST':
        form = EmployerProfileForm(request.POST, request.FILES, instance=employer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('myapp:employer_profile')
    else:
        form = EmployerProfileForm(instance=employer)
    
    return render(request, 'myapp/employer_profile.html', {
        'form': form,
        'employer': employer
    })