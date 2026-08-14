"""Django settings rendered by the BU-ISCIII deployment library.

This is an application-owned template. Keep the exact Django applications and
project behavior here; deployment-specific values are replaced from the
selected production or test installation settings file.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# The renderer replaces this complete line and preserves the existing generated
# value during upgrades. Never commit a real production secret here.
SECRET_KEY = "PLACEHOLDER"
DEBUG = djangodebug
ALLOWED_HOSTS = [
    host.strip() for host in "djangoallowedhosts".split(",") if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in "djangocsrftrustedorigins".split(",") if origin.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_plotly_dash.apps.DjangoPlotlyDashConfig",
    "django_crontab",
    "core",
    "dashboard",
    "docs",
    "django_extensions",
    "rest_framework",
    "drf_spectacular",
    # django-cleanup must follow the applications whose files it manages.
    "django_cleanup",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_plotly_dash.middleware.BaseMiddleware",
    "django_plotly_dash.middleware.ExternalRedirectionMiddleware",
]

ROOT_URLCONF = "relecov_platform.urls"
WSGI_APPLICATION = "relecov_platform.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "docs.utils.context_processors.docs_current_path",
            ],
        },
    }
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "djangodbname",
        "USER": "djangouser",
        "PASSWORD": "djangopass",
        "HOST": "djangohost",
        "PORT": "djangoport",
        "CONN_MAX_AGE": dbconnmaxage,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Relecov Platform API",
    "DESCRIPTION": "REST API to access Relecov Platform",
    "VERSION": "1.0",
    "SERVE_INCLUDE_SCHEMA": True,
    "GENERIC_ADDITIONAL_PROPERTIES": "dict",
}

SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {"basic": {"type": "basic"}},
}

# Dash views are embedded in application pages.
X_FRAME_OPTIONS = "SAMEORIGIN"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = False

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django_plotly_dash.finders.DashAssetFinder",
    "django_plotly_dash.finders.DashAppDirectoryFinder",
    "core.finders.DashComponentFinderNoDuplicates",
]

PLOTLY_COMPONENTS = [
    "dpd_components",
    "dash_bootstrap_components",
    "dash_daq",
    "dash_bio",
]

PLOTLY_DASH = {
    "view_decorator": "core.dash_access.selective_login_required",
    # LocMemCache is process-local and breaks iframe initial state when the
    # deployment runs multiple Gunicorn workers.
    "cache_arguments": False,
    "serve_locally": True,
}

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "/documents/"
MEDIA_ROOT = BASE_DIR / "documents"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "emailhostserver"
EMAIL_PORT = emailport
EMAIL_HOST_USER = "emailhostuser"
EMAIL_HOST_PASSWORD = "emailhostpassword"
EMAIL_USE_TLS = emailhosttls

LOGIN_REDIRECT_URL = "/intranet/"

LOG_CRONTAB_FILE = BASE_DIR / "logs" / "crontab.log"
CRONJOBS = [
    (
        "0 0 * * *",
        "dashboard.cron.update_search_samples_summary",
        f">>{LOG_CRONTAB_FILE}",
    ),
    (
        "10 0 1 * *",
        "dashboard.cron.update_graphic_json_data",
        f">>{LOG_CRONTAB_FILE}",
    ),
]
CRONTAB_COMMAND_SUFFIX = "2>&1"

# Optional upload limit in bytes. Django's default is 2.5 MiB.
# DATA_UPLOAD_MAX_MEMORY_SIZE = 10_000_000

# Apache overwrites this header before forwarding requests to Django.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
