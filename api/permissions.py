from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class IsEmployer(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'employer')

class IsJobSeeker(permissions.BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'jobseeker')

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user

class IsCompanyOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if hasattr(request.user, 'employer'):
            return obj.employer == request.user.employer
        return False

class IsJobOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'employer'):
            return False
        return request.user.employer in obj.company.employers.all()

class IsApplicationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'employer'):
            return False
        return request.user.employer in obj.job.company.employers.all()

class IsSearchLogOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsJobViewLogOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsJobAlertOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsSavedJobOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.jobseeker.user == request.user

class IsJobMatchOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.job_seeker.user == request.user

class IsSavedSearchOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsJobMetricsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if hasattr(request.user, 'employer'):
            return obj.job.company.employer == request.user.employer
        return False

class IsNotificationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsJobApplicationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(request.user, 'employer'):
            return False
        return request.user.employer in obj.job.company.employers.all() 