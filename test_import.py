try:
    import django_axes
    print("django-axes imported successfully")
    print(f"django-axes version: {django_axes.__version__}")
except ImportError as e:
    print(f"Error importing django-axes: {e}") 