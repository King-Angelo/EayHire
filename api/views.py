from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.contrib.auth.models import User
from django.db import models
from rest_framework.filters import SearchFilter, OrderingFilter

from .serializers import *
from myapp.models import *
from .permissions import *
from .filters import *

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering = ['-created_at']

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class JobCategoryViewSet(BaseViewSet):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer

class SkillViewSet(BaseViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

class BenefitViewSet(BaseViewSet):
    queryset = Benefit.objects.all()
    serializer_class = BenefitSerializer

class CompanyViewSet(BaseViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'employer'):
            return Company.objects.filter(employer=self.request.user.employer)
        return Company.objects.all()

class JobPostingViewSet(BaseViewSet):
    queryset = JobPosting.objects.all()
    serializer_class = JobPostingSerializer
    filterset_class = JobPostingFilter
    search_fields = ['title', 'description', 'requirements', 'location']
    ordering_fields = ['created_at', 'updated_at', 'salary_min', 'salary_max', 'deadline']

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'employer'):
            return queryset.filter(company__employer=self.request.user.employer)
        return queryset.filter(is_active=True)

    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        job = self.get_object()
        if hasattr(request.user, 'jobseeker'):
            application = JobApplication.objects.create(
                job=job,
                applicant=request.user.jobseeker,
                cover_letter=request.data.get('cover_letter', ''),
                resume=request.data.get('resume', None)
            )
            serializer = JobApplicationSerializer(application)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(
            {'error': 'Only job seekers can apply for jobs'},
            status=status.HTTP_403_FORBIDDEN
        )

class EmployerViewSet(BaseViewSet):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer
    filterset_class = EmployerFilter
    search_fields = ['user__username', 'user__email', 'company__name']
    ordering_fields = ['created_at', 'updated_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'employer'):
            return queryset.filter(user=self.request.user)
        return queryset.none()

class JobSeekerViewSet(BaseViewSet):
    queryset = JobSeeker.objects.all()
    serializer_class = JobSeekerSerializer
    filterset_class = JobSeekerFilter
    search_fields = ['user__username', 'user__email', 'location', 'skills__name']
    ordering_fields = ['created_at', 'updated_at', 'expected_salary']

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'jobseeker'):
            return queryset.filter(user=self.request.user)
        return queryset.none()

class JobApplicationViewSet(BaseViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer
    filterset_class = JobApplicationFilter
    search_fields = ['job__title', 'applicant__user__username', 'cover_letter']
    ordering_fields = ['applied_at', 'updated_at', 'match_score']

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'employer'):
            return queryset.filter(job__company__employer=self.request.user.employer)
        elif hasattr(self.request.user, 'jobseeker'):
            return queryset.filter(applicant=self.request.user.jobseeker)
        return queryset.none()

class JobAlertViewSet(BaseViewSet):
    queryset = JobAlert.objects.all()
    serializer_class = JobAlertSerializer

    def get_queryset(self):
        return JobAlert.objects.filter(user=self.request.user)

class SavedJobViewSet(BaseViewSet):
    queryset = SavedJob.objects.all()
    serializer_class = SavedJobSerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'jobseeker'):
            return SavedJob.objects.filter(jobseeker=self.request.user.jobseeker)
        return SavedJob.objects.none()

class JobMatchViewSet(BaseViewSet):
    queryset = JobMatch.objects.all()
    serializer_class = JobMatchSerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'jobseeker'):
            return JobMatch.objects.filter(job_seeker=self.request.user.jobseeker)
        return JobMatch.objects.none()

class SearchLogViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavedSearchSerializer
    
    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

class SavedSearchViewSet(BaseViewSet):
    queryset = SavedSearch.objects.all()
    serializer_class = SavedSearchSerializer

    def get_queryset(self):
        return SavedSearch.objects.filter(user=self.request.user)

class JobMetricsViewSet(BaseViewSet):
    queryset = JobMetrics.objects.all()
    serializer_class = JobMetricsSerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'employer'):
            return JobMetrics.objects.filter(job__company__employer=self.request.user.employer)
        return JobMetrics.objects.none()

class JobViewLogViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = JobPostingSerializer
    
    def get_queryset(self):
        return JobViewLog.objects.filter(user=self.request.user)

class NotificationViewSet(BaseViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'All notifications marked as read'})

class ApplicationHistoryViewSet(BaseViewSet):
    queryset = ApplicationHistory.objects.all()
    serializer_class = ApplicationHistorySerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'employer'):
            return ApplicationHistory.objects.filter(
                application__job__company__employer=self.request.user.employer
            )
        elif hasattr(self.request.user, 'jobseeker'):
            return ApplicationHistory.objects.filter(
                application__applicant=self.request.user.jobseeker
            )
        return ApplicationHistory.objects.none()

class JobPostingMetricsViewSet(BaseViewSet):
    queryset = JobPosting.objects.all()
    serializer_class = JobPostingSerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'employer'):
            return JobPosting.objects.filter(company__employer=self.request.user.employer)
        return JobPosting.objects.none()

    def list(self, request):
        queryset = self.get_queryset()
        metrics = {
            'total_jobs': queryset.count(),
            'active_jobs': queryset.filter(is_active=True).count(),
            'applications_per_job': queryset.annotate(
                application_count=models.Count('applications')
            ).values('id', 'title', 'application_count'),
            'views_per_job': queryset.annotate(
                view_count=models.Count('view_logs')
            ).values('id', 'title', 'view_count')
        }
        return Response(metrics)

class ApplicationMetricsViewSet(BaseViewSet):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'employer'):
            return JobApplication.objects.filter(job__company__employer=self.request.user.employer)
        elif hasattr(self.request.user, 'jobseeker'):
            return JobApplication.objects.filter(applicant=self.request.user.jobseeker)
        return JobApplication.objects.none()

    def list(self, request):
        queryset = self.get_queryset()
        metrics = {
            'total_applications': queryset.count(),
            'applications_by_status': queryset.values('status').annotate(
                count=models.Count('id')
            ),
            'applications_by_job': queryset.values('job__title').annotate(
                count=models.Count('id')
            ),
            'average_match_score': queryset.aggregate(
                avg_score=models.Avg('match_score')
            )
        }
        return Response(metrics)

class JobSeekerMetricsViewSet(BaseViewSet):
    queryset = JobSeeker.objects.all()
    serializer_class = JobSeekerSerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'jobseeker'):
            return JobSeeker.objects.filter(user=self.request.user)
        return JobSeeker.objects.none()

    def list(self, request):
        queryset = self.get_queryset()
        metrics = {
            'total_applications': queryset.annotate(
                application_count=models.Count('applications')
            ).values('id', 'user__username', 'application_count'),
            'saved_jobs': queryset.annotate(
                saved_job_count=models.Count('saved_jobs')
            ).values('id', 'user__username', 'saved_job_count'),
            'job_matches': queryset.annotate(
                match_count=models.Count('job_matches')
            ).values('id', 'user__username', 'match_count')
        }
        return Response(metrics)

class EmployerMetricsViewSet(BaseViewSet):
    queryset = Employer.objects.all()
    serializer_class = EmployerSerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'employer'):
            return Employer.objects.filter(user=self.request.user)
        return Employer.objects.none()

    def list(self, request):
        queryset = self.get_queryset()
        metrics = {
            'total_jobs': queryset.annotate(
                job_count=models.Count('company__jobposting')
            ).values('id', 'user__username', 'job_count'),
            'total_applications': queryset.annotate(
                application_count=models.Count('company__jobposting__applications')
            ).values('id', 'user__username', 'application_count'),
            'average_match_score': queryset.annotate(
                avg_score=models.Avg('company__jobposting__applications__match_score')
            ).values('id', 'user__username', 'avg_score')
        }
        return Response(metrics)

class CompanyMetricsViewSet(BaseViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    def get_queryset(self):
        if hasattr(self.request.user, 'employer'):
            return Company.objects.filter(employer=self.request.user.employer)
        return Company.objects.none()

    def list(self, request):
        queryset = self.get_queryset()
        metrics = {
            'total_jobs': queryset.annotate(
                job_count=models.Count('jobposting')
            ).values('id', 'name', 'job_count'),
            'total_applications': queryset.annotate(
                application_count=models.Count('jobposting__applications')
            ).values('id', 'name', 'application_count'),
            'average_match_score': queryset.annotate(
                avg_score=models.Avg('jobposting__applications__match_score')
            ).values('id', 'name', 'avg_score')
        }
        return Response(metrics)
