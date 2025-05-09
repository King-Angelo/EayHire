"""
# All models have been moved to myapp/models.py
# This file is kept for historical purposes and to maintain migrations
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg, Count, F, Q
from django.conf import settings
from myapp.models import (
    JobCategory, Skill, Benefit, Company, JobPosting, JobMetrics,
    JobSeeker, Employer, JobApplication, SavedJob, JobAlert, Notification,
    JobMatch, SavedSearch, ApplicationHistory, ApplicationStatusHistory,
    PageView, UserAction, AnalyticsReport, JobViewLog
)

class JobSeekerProxy(JobSeeker):
    class Meta:
        proxy = True

class EmployerProxy(Employer):
    class Meta:
        proxy = True

class JobPostingProxy(JobPosting):
    class Meta:
        proxy = True

class JobApplicationProxy(JobApplication):
    class Meta:
        proxy = True

class SavedJobProxy(SavedJob):
    class Meta:
        proxy = True

class JobAlertProxy(JobAlert):
    class Meta:
        proxy = True

class ApplicationStatusHistoryProxy(ApplicationStatusHistory):
    class Meta:
        proxy = True

class SavedSearchProxy(SavedSearch):
    class Meta:
        proxy = True

class JobMatchProxy(JobMatch):
    class Meta:
        proxy = True

class JobMetricsProxy(JobMetrics):
    class Meta:
        proxy = True

class JobViewLogProxy(JobViewLog):
    class Meta:
        proxy = True

class NotificationProxy(Notification):
    class Meta:
        proxy = True

class PageViewProxy(PageView):
    class Meta:
        proxy = True

class UserActionProxy(UserAction):
    class Meta:
        proxy = True

class AnalyticsReportProxy(AnalyticsReport):
    class Meta:
        proxy = True
