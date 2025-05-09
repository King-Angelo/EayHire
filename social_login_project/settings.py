# django-axes settings
AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5  # Number of failed login attempts before lockout
AXES_COOLOFF_TIME = 1  # Lockout time in hours
AXES_LOCKOUT_TEMPLATE = 'account/lockout.html'
AXES_RESET_ON_SUCCESS = True
AXES_DISABLE_ACCESS_LOG = False
AXES_LOGOUT_REDIRECT_URL = 'account_login'
AXES_VERBOSE = True
AXES_LOCKOUT_PARAMETERS = [["ip_address", "user_agent"]]
AXES_META_PRECEDENCE_ORDER = [
    'HTTP_X_FORWARDED_FOR',
    'REMOTE_ADDR',
]
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
AXES_SESSION_HASH = True 