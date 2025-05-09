from django.apps import AppConfig


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    verbose_name = 'Job Portal'

    def ready(self):
        import myapp.signals  # Import signals when app is ready
