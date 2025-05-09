from django.urls import path
from . import views
import myapp.views as myapp_views
from django.views.generic import TemplateView
from django.shortcuts import redirect

app_name = 'myapp'

urlpatterns = [
    path('', lambda request: redirect('jobs:home'), name='root_redirect'),
    path('employer/register/', views.EmployerRegistrationView.as_view(), name='employer_register'),
    path('jobseeker/register/', views.JobSeekerRegistrationView.as_view(), name='jobseeker_register'),
    path('employer/dashboard/', views.EmployerDashboardView.as_view(), name='employer_dashboard'),
    path('employer/jobs/', views.employer_jobs, name='employer_jobs'),
    path('jobseeker/profile/edit/', myapp_views.JobseekerProfileEditView.as_view(), name='jobseeker_profile_edit'),
    path("verified/", TemplateView.as_view(template_name="account/verified.html"), name="verified"),
    path('contact/', views.contact_new, name='contact'),
    path('employer/search/', views.employer_search, name='employer_search'),
    path('employer/profile/', views.employer_profile, name='employer_profile'),
]