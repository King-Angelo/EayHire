import os
from datetime import timedelta

# Ensure SECRET_KEY is set via an environment variable
SECRET_KEY = os.getenv('SECRET_KEY', 'p34rgsp_ggzn6=%ikegz&_v3(#^plke+jn$w!2o%&6umhonpdk')  # Replace with your default key or use an env variable

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # Access token lifetime
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),  # Refresh token lifetime
    'ROTATE_REFRESH_TOKENS': False,  # Set to False if you do not want to rotate refresh tokens
    'BLACKLIST_AFTER_ROTATION': True,  # Blacklist refresh tokens after rotation
    'ALGORITHM': 'HS256',  # JWT algorithm
    'SIGNING_KEY': SECRET_KEY,  # Use the SECRET_KEY to sign the tokens
    'VERIFYING_KEY': None,  # You can set this if you have a public key to verify tokens
    'AUTH_HEADER_TYPES': ('Bearer',),  # Default auth header types
    'USER_ID_FIELD': 'id',  # Field in your user model to represent user ID
    'USER_ID_CLAIM': 'user'
}