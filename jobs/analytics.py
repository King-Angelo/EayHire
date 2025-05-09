from django.db import models
from django.db.models import Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta

class AnalyticsManager:
    @staticmethod
    def get_user_engagement_metrics(user, days=30):
        """Calculate user engagement metrics over a period"""
        start_date = timezone.now() - timedelta(days=days)
        from .models import JobViewLog, Application, SavedJob, JobAlert
        
        return {
            'view_count': JobViewLog.objects.filter(
                user=user,
                viewed_at__gte=start_date
            ).count(),
            'application_count': Application.objects.filter(
                applicant__user=user,
                applied_at__gte=start_date
            ).count(),
            'saved_jobs': SavedJob.objects.filter(
                job_seeker__user=user,
                saved_at__gte=start_date
            ).count(),
            'alert_count': JobAlert.objects.filter(
                job_seeker__user=user,
                created_at__gte=start_date
            ).count()
        }

    @staticmethod
    def get_platform_metrics(days=30):
        """Get overall platform metrics"""
        start_date = timezone.now() - timedelta(days=days)
        from .models import JobPosting, Application, Employer, JobSeeker, UserSession, UserAction
        
        # Get basic metrics
        metrics = {
            'total_jobs': JobPosting.objects.filter(
                created_at__gte=start_date
            ).count(),
            'total_applications': Application.objects.filter(
                applied_at__gte=start_date
            ).count(),
            'new_employers': Employer.objects.filter(
                created_at__gte=start_date
            ).count(),
            'new_job_seekers': JobSeeker.objects.filter(
                created_at__gte=start_date
            ).count()
        }
        
        # Calculate application success rate
        total_applications = Application.objects.filter(
            applied_at__gte=start_date
        ).count()
        successful_applications = Application.objects.filter(
            applied_at__gte=start_date,
            status='accepted'
        ).count()
        metrics['application_success_rate'] = (
            successful_applications / total_applications * 100 
            if total_applications > 0 else 0
        )
        
        # Calculate engagement score
        sessions = UserSession.objects.filter(
            start_time__gte=start_date
        )
        avg_pages = sessions.aggregate(avg=Avg('pages_viewed'))['avg'] or 0
        avg_actions = sessions.aggregate(avg=Avg('actions_performed'))['avg'] or 0
        
        # Get action distribution
        action_counts = UserAction.objects.filter(
            action_time__gte=start_date
        ).values('action_type').annotate(
            count=Count('id')
        )
        
        # Calculate engagement score (0-100)
        engagement_score = min(
            (avg_pages * 10 + avg_actions * 20) / 3,
            100
        )
        
        # Calculate engagement growth
        previous_start = start_date - timedelta(days=days)
        previous_sessions = UserSession.objects.filter(
            start_time__gte=previous_start,
            start_time__lt=start_date
        )
        previous_avg_pages = previous_sessions.aggregate(
            avg=Avg('pages_viewed')
        )['avg'] or 0
        previous_avg_actions = previous_sessions.aggregate(
            avg=Avg('actions_performed')
        )['avg'] or 0
        previous_engagement = (previous_avg_pages * 10 + previous_avg_actions * 20) / 3
        
        engagement_growth = (
            (engagement_score - previous_engagement) / previous_engagement * 100
            if previous_engagement > 0 else 0
        )
        
        metrics.update({
            'engagement_score': engagement_score,
            'engagement_growth': engagement_growth,
            'avg_pages_per_session': avg_pages,
            'avg_actions_per_session': avg_actions,
            'action_distribution': {
                action['action_type']: action['count']
                for action in action_counts
            }
        })
        
        return metrics

    @staticmethod
    def get_trend_analysis(model, date_field, group_by, days=30):
        """Generic trend analysis function"""
        start_date = timezone.now() - timedelta(days=days)
        return model.objects.filter(**{
            f'{date_field}__gte': start_date
        }).annotate(
            date=models.functions.TruncDate(date_field)
        ).values('date', *group_by).annotate(
            count=Count('id')
        ).order_by('date') 

    @staticmethod
    def get_job_performance_metrics(job_ids=None, days=30):
        """Get performance metrics for specific jobs or all jobs"""
        from .models import JobPosting, Application, JobViewLog
        start_date = timezone.now() - timedelta(days=days)
        
        jobs = JobPosting.objects.all()
        if job_ids:
            jobs = jobs.filter(id__in=job_ids)
            
        metrics = []
        for job in jobs:
            views = JobViewLog.objects.filter(
                job=job,
                viewed_at__gte=start_date
            ).count()
            
            applications = Application.objects.filter(
                job=job,
                applied_at__gte=start_date
            )
            
            total_applications = applications.count()
            accepted_applications = applications.filter(status='accepted').count()
            
            metrics.append({
                'job_id': job.id,
                'job_title': job.title,
                'views': views,
                'applications': total_applications,
                'conversion_rate': (total_applications / views * 100) if views > 0 else 0,
                'success_rate': (accepted_applications / total_applications * 100) if total_applications > 0 else 0,
                'cost_per_application': job.cost_per_day * days / total_applications if total_applications > 0 else 0,
                'time_to_fill': job.time_to_fill.days if job.time_to_fill else None,
                'source_distribution': {
                    source['source']: source['count']
                    for source in JobViewLog.objects.filter(
                        job=job,
                        viewed_at__gte=start_date
                    ).values('source').annotate(count=Count('id'))
                }
            })
            
        return metrics

    @staticmethod
    def get_application_funnel_metrics(days=30):
        """Get application funnel metrics"""
        from .models import JobPosting, Application, JobViewLog, SearchLog
        start_date = timezone.now() - timedelta(days=days)
        
        # Get funnel stages
        search_impressions = SearchLog.objects.filter(
            searched_at__gte=start_date
        ).count()
        
        job_views = JobViewLog.objects.filter(
            viewed_at__gte=start_date
        ).count()
        
        unique_views = JobViewLog.objects.filter(
            viewed_at__gte=start_date
        ).values('job', 'session_id').distinct().count()
        
        applications = Application.objects.filter(
            applied_at__gte=start_date
        )
        total_applications = applications.count()
        
        # Calculate conversion rates
        view_rate = (job_views / search_impressions * 100) if search_impressions > 0 else 0
        application_rate = (total_applications / job_views * 100) if job_views > 0 else 0
        
        # Get status distribution
        status_distribution = {
            status['status']: status['count']
            for status in applications.values('status').annotate(count=Count('id'))
        }
        
        # Get time-to-fill distribution
        time_to_fill = applications.filter(
            status='accepted'
        ).annotate(
            fill_time=F('status_history__changed_at') - F('applied_at')
        ).values('fill_time').annotate(
            count=Count('id')
        ).order_by('fill_time')
        
        return {
            'funnel_stages': {
                'search_impressions': search_impressions,
                'job_views': job_views,
                'unique_views': unique_views,
                'applications': total_applications
            },
            'conversion_rates': {
                'view_rate': view_rate,
                'application_rate': application_rate
            },
            'status_distribution': status_distribution,
            'time_to_fill_distribution': {
                str(item['fill_time']): item['count']
                for item in time_to_fill
            }
        }