from django.db import models
from django.db.models import Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta

class AnalyticsManager:
    @staticmethod
    def get_user_engagement_metrics(user, days=30):
        """Calculate user engagement metrics over a period"""
        start_date = timezone.now() - timedelta(days=days)
        from .models import JobViewLog, Application, SavedJob, JobAlert, UserSession, UserAction
        
        # Get user sessions
        sessions = UserSession.objects.filter(
            user=user,
            start_time__gte=start_date
        )
        
        # Calculate average session metrics
        session_metrics = sessions.aggregate(
            avg_pages=Avg('pages_viewed'),
            avg_actions=Avg('actions_performed')
        )
        
        # Get action distribution
        action_counts = UserAction.objects.filter(
            session__user=user,
            action_time__gte=start_date
        ).values('action_type').annotate(
            count=Count('id')
        )
        
        # Calculate engagement score
        avg_pages = session_metrics['avg_pages'] or 0
        avg_actions = session_metrics['avg_actions'] or 0
        engagement_score = (avg_pages * 10 + avg_actions * 20) / 3
        
        # Calculate engagement growth
        previous_start = start_date - timedelta(days=days)
        previous_sessions = UserSession.objects.filter(
            user=user,
            start_time__gte=previous_start,
            start_time__lt=start_date
        )
        previous_metrics = previous_sessions.aggregate(
            avg_pages=Avg('pages_viewed'),
            avg_actions=Avg('actions_performed')
        )
        previous_score = ((previous_metrics['avg_pages'] or 0) * 10 + 
                         (previous_metrics['avg_actions'] or 0) * 20) / 3
        
        engagement_growth = (
            (engagement_score - previous_score) / previous_score * 100
            if previous_score > 0 else 0
        )
        
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
            ).count(),
            'engagement_score': engagement_score,
            'engagement_growth': engagement_growth,
            'avg_pages_per_session': avg_pages,
            'avg_actions_per_session': avg_actions,
            'action_distribution': {
                action['action_type']: action['count']
                for action in action_counts
            }
        }

    @staticmethod
    def get_platform_metrics(days=30):
        """Get overall platform metrics"""
        from .models import JobPosting, Application, JobSeeker, Company, UserSession
        from django.contrib.auth.models import User
        
        start_date = timezone.now() - timedelta(days=days)
        
        # User metrics
        total_users = User.objects.count()
        new_users = User.objects.filter(
            date_joined__gte=start_date
        ).count()
        
        # Calculate user growth
        previous_users = User.objects.filter(
            date_joined__lt=start_date
        ).count()
        user_growth = (
            (total_users - previous_users) / previous_users * 100
            if previous_users > 0 else 0
        )
        
        # Job metrics
        active_jobs = JobPosting.objects.filter(
            is_active=True
        ).count()
        
        new_jobs = JobPosting.objects.filter(
            created_at__gte=start_date
        ).count()
        
        # Application metrics
        applications = Application.objects.filter(
            applied_at__gte=start_date
        )
        total_applications = applications.count()
        
        accepted_applications = applications.filter(
            status='accepted'
        ).count()
        
        # Calculate application rate
        application_rate = (
            accepted_applications / total_applications * 100
            if total_applications > 0 else 0
        )
        
        # Engagement metrics
        sessions = UserSession.objects.filter(
            start_time__gte=start_date
        )
        
        session_metrics = sessions.aggregate(
            avg_pages=Avg('pages_viewed'),
            avg_actions=Avg('actions_performed')
        )
        
        avg_pages = session_metrics['avg_pages'] or 0
        avg_actions = session_metrics['avg_actions'] or 0
        engagement_score = (avg_pages * 10 + avg_actions * 20) / 3
        
        # Calculate engagement growth
        previous_start = start_date - timedelta(days=days)
        previous_sessions = UserSession.objects.filter(
            start_time__gte=previous_start,
            start_time__lt=start_date
        )
        previous_metrics = previous_sessions.aggregate(
            avg_pages=Avg('pages_viewed'),
            avg_actions=Avg('actions_performed')
        )
        previous_score = ((previous_metrics['avg_pages'] or 0) * 10 + 
                         (previous_metrics['avg_actions'] or 0) * 20) / 3
        
        engagement_growth = (
            (engagement_score - previous_score) / previous_score * 100
            if previous_score > 0 else 0
        )
        
        return {
            'total_users': total_users,
            'new_users': new_users,
            'user_growth': user_growth,
            'active_jobs': active_jobs,
            'new_jobs': new_jobs,
            'total_applications': total_applications,
            'accepted_applications': accepted_applications,
            'application_rate': application_rate,
            'engagement_score': engagement_score,
            'engagement_growth': engagement_growth,
            'avg_pages_per_session': avg_pages,
            'avg_actions_per_session': avg_actions
        }

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