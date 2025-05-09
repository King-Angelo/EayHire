from django.contrib import admin
from .models import (
    JobCategory, Skill, Benefit, JobPosting, Company, JobSeeker,
    JobApplication, JobAlert, SavedJob, SearchLog, JobViewLog,
    UserSession, PageView, UserAction, AnalyticsReport
)

@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'created_at', 'updated_at')
    list_filter = ('category',)
    search_fields = ('name', 'description')

@admin.register(Benefit)
class BenefitAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name', 'description')

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'experience_level', 'location', 'is_active', 'created_at')
    list_filter = ('job_type', 'experience_level', 'is_active', 'is_featured')
    search_fields = ('title', 'company__name', 'location')
    filter_horizontal = ('required_skills', 'preferred_skills', 'benefits')
    date_hierarchy = 'created_at'

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'location', 'founded_year', 'employee_count')
    search_fields = ('name', 'industry', 'location')
    list_filter = ('industry',)

@admin.register(JobSeeker)
class JobSeekerAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_level', 'location', 'is_available')
    list_filter = ('experience_level', 'is_available')
    search_fields = ('user__username', 'user__email', 'location')
    filter_horizontal = ('skills',)

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'applied_at', 'match_score')
    list_filter = ('status', 'applied_at')
    search_fields = ('applicant__user__username', 'job__title')
    date_hierarchy = 'applied_at'

@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ('job_seeker', 'keywords', 'frequency', 'is_active', 'last_sent')
    list_filter = ('frequency', 'is_active')
    search_fields = ('job_seeker__user__username', 'keywords')

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('job_seeker', 'job', 'saved_at')
    search_fields = ('job_seeker__user__username', 'job__title')
    date_hierarchy = 'saved_at'

@admin.register(SearchLog)
class SearchLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'results_count', 'searched_at')
    search_fields = ('user__username', 'query')
    date_hierarchy = 'searched_at'

@admin.register(JobViewLog)
class JobViewLogAdmin(admin.ModelAdmin):
    list_display = ('job', 'user', 'session_id', 'source', 'viewed_at')
    list_filter = ('source',)
    search_fields = ('job__title', 'user__username', 'session_id')
    date_hierarchy = 'viewed_at'

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_time', 'end_time', 'pages_viewed', 'actions_performed')
    search_fields = ('user__username', 'session_key')
    date_hierarchy = 'start_time'

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ('session', 'page_url', 'view_time', 'time_spent')
    search_fields = ('session__user__username', 'page_url')
    date_hierarchy = 'view_time'

@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('session', 'action_type', 'action_time')
    list_filter = ('action_type',)
    search_fields = ('session__user__username',)
    date_hierarchy = 'action_time'

@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'created_by', 'schedule_frequency', 'is_active', 'last_generated')
    list_filter = ('report_type', 'schedule_frequency', 'is_active')
    search_fields = ('name', 'description', 'created_by__username')
    filter_horizontal = ('recipients',)
    date_hierarchy = 'created_at'
