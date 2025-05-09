app.conf.beat_schedule = {
    'send-saved-search-notifications': {
        'task': 'jobs.tasks.send_saved_search_notifications',
        'schedule': crontab(hour='*/4'),  # Run every 4 hours
    },
    # ... other scheduled tasks ...
} 