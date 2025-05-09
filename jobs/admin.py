from django.contrib import admin
from .models import (
    JobSeekerProxy, EmployerProxy, JobPostingProxy,
    JobApplicationProxy, JobViewLogProxy
)

@admin.register(JobSeekerProxy)
class JobSeekerAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_level', 'location', 'created_at')
    search_fields = ('user__username', 'user__email', 'location')
    list_filter = ('experience_level', 'created_at')

@admin.register(EmployerProxy)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'created_at')
    search_fields = ('user__username', 'user__email', 'company__name')
    list_filter = ('created_at',)

@admin.register(JobPostingProxy)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'is_active', 'created_at')
    search_fields = ('title', 'company__name', 'description')
    list_filter = ('is_active', 'created_at')

@admin.register(JobApplicationProxy)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'applicant', 'status', 'applied_at')
    search_fields = ('job__title', 'applicant__user__username')
    list_filter = ('status', 'applied_at')

@admin.register(JobViewLogProxy)
class JobViewLogAdmin(admin.ModelAdmin):
    list_display = ('job', 'user', 'viewed_at', 'source')
    search_fields = ('job__title', 'user__username')
    list_filter = ('source', 'viewed_at')
