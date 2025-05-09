from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    UserViewSet,
    JobCategoryViewSet,
    SkillViewSet,
    BenefitViewSet,
    CompanyViewSet,
    JobPostingViewSet,
    JobMetricsViewSet,
    JobSeekerViewSet,
    EmployerViewSet,
    JobApplicationViewSet,
    SavedJobViewSet,
    JobAlertViewSet,
    NotificationViewSet,
    JobMatchViewSet,
    SavedSearchViewSet,
    ApplicationHistoryViewSet,
)

router = DefaultRouter()

# Core Models
router.register(r'users', UserViewSet)
router.register(r'job-categories', JobCategoryViewSet)
router.register(r'skills', SkillViewSet)
router.register(r'benefits', BenefitViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'job-postings', JobPostingViewSet)
router.register(r'job-metrics', JobMetricsViewSet)
router.register(r'job-seekers', JobSeekerViewSet)
router.register(r'employers', EmployerViewSet)
router.register(r'job-applications', JobApplicationViewSet)
router.register(r'saved-jobs', SavedJobViewSet)
router.register(r'job-alerts', JobAlertViewSet)
router.register(r'notifications', NotificationViewSet)
router.register(r'job-matches', JobMatchViewSet)
router.register(r'saved-searches', SavedSearchViewSet)
router.register(r'application-history', ApplicationHistoryViewSet)

urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Include all router URLs
    path('', include(router.urls)),
    
    # Additional endpoints
    path('job-postings/<int:pk>/apply/', JobPostingViewSet.as_view({'post': 'apply'}), name='job-posting-apply'),
    path('notifications/<int:pk>/mark-as-read/', NotificationViewSet.as_view({'post': 'mark_as_read'}), name='notification-mark-as-read'),
    path('notifications/mark-all-read/', NotificationViewSet.as_view({'post': 'mark_all_read'}), name='notification-mark-all-read'),
] 