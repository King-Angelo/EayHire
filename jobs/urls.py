from django.urls import path
from django.shortcuts import redirect
from . import views
from myapp.views import JobSeekerRegistrationView, EmployerRegistrationView
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.urls import include
from .views import SaveJobView
from jobs.views import ResumeView, ApplicationStatusActionView

app_name = 'jobs'

def redirect_to_dashboard(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'myapp_employer'):
            return redirect('jobs:employer_dashboard')
        elif hasattr(request.user, 'myapp_jobseeker'):
            return redirect('jobs:jobseeker_dashboard')
    return redirect('jobs:job_list')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Removing duplicate accounts/ URL pattern
    # path('accounts/', include('allauth.urls')),
    
    # Role Selection
    path('role-selection/', views.RoleSelectionView.as_view(), name='role_selection'),
    
    # Homepage and Landing Page
    path('', views.home, name='home'),
    path('list/', views.JobListView.as_view(), name='job_list'),
    
    # Job Details and Management
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('jobs/create/', views.JobPostingCreateView.as_view(), name='job_create'),
    path('jobs/<int:pk>/edit/', views.JobPostingUpdateView.as_view(), name='job_edit'),
    path('jobs/<int:pk>/delete/', views.JobPostingDeleteView.as_view(), name='job_delete'),
    path('jobs/<int:pk>/toggle-status/', views.JobToggleStatusView.as_view(), name='job_toggle_status'),
    path('employer/jobs/', views.EmployerJobListView.as_view(), name='employer_jobs'),
    
    # Applications
    path('applications/', views.ApplicationListView.as_view(), name='application_list'),
    path('applications/<int:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('applications/<int:pk>/update/', views.ApplicationUpdateView.as_view(), name='application_update'),
    path('applications/<int:pk>/delete/', views.ApplicationDeleteView.as_view(), name='application_delete'),
    path('applications/<int:application_id>/status/', ApplicationStatusActionView.as_view(), name='application_status_action'),
    
    # Registration - Using myapp views
    path('employer/register/', EmployerRegistrationView.as_view(), name='employer_register'),
    path('jobseeker/register/', JobSeekerRegistrationView.as_view(), name='jobseeker_register'),
    
    # Dashboards
    path('dashboard/', redirect_to_dashboard, name='dashboard'),
    path('employer/dashboard/', views.EmployerDashboardView.as_view(), name='employer_dashboard'),
    path('jobseeker/dashboard/', views.JobSeekerDashboardView.as_view(), name='jobseeker_dashboard'),
    
    # Profile Management
    path('jobseeker/profile/edit/', views.JobSeekerProfileEditView.as_view(), name='jobseeker_profile_edit'),
    
    # Saved Jobs
    path('saved-jobs/', views.SavedJobListView.as_view(), name='saved_job_list'),
    path('saved-jobs/<int:pk>/', views.SavedJobDetailView.as_view(), name='saved_job_detail'),
    path('saved-jobs/<int:pk>/delete/', views.SavedJobDeleteView.as_view(), name='saved_job_delete'),
    
    # Job Alerts
    path('job-alerts/', views.JobAlertListView.as_view(), name='job_alert_list'),
    path('job-alerts/create/', views.JobAlertCreateView.as_view(), name='job_alert_create'),
    path('job-alerts/<int:pk>/', views.JobAlertDetailView.as_view(), name='job_alert_detail'),
    path('job-alerts/<int:pk>/update/', views.JobAlertUpdateView.as_view(), name='job_alert_update'),
    path('job-alerts/<int:pk>/delete/', views.JobAlertDeleteView.as_view(), name='job_alert_delete'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<int:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/<int:pk>/update/', views.NotificationUpdateView.as_view(), name='notification_update'),
    path('notifications/<int:pk>/delete/', views.NotificationDeleteView.as_view(), name='notification_delete'),
    path('notifications/settings/', views.NotificationSettingsView.as_view(), name='notification_settings'),
    path('notifications/mark-read/', views.NotificationMarkReadView.as_view(), name='mark_notifications_read'),
    
    # Analytics
    path('employer/analytics/', views.EmployerAnalyticsDashboardView.as_view(), name='employer_analytics'),
    
    # Job Application
    path('jobs/<int:job_id>/apply/', views.ApplicationCreateView.as_view(), name='job_apply'),
    path('save-job/', SaveJobView.as_view(), name='save_job'),
    path('ajax/search/', views.JobAjaxSearchView.as_view(), name='ajax_job_search'),
    path('search/', views.JobSearchResultsView.as_view(), name='job_search_results'),
    
    # Resume View
    path('resume/<int:application_id>/', ResumeView.as_view(), name='view_resume'),
]
