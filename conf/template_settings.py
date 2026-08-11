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
    origin.strip()
    for origin in "djangocsrftrustedorigins".split(",")
    if origin.strip()
]

# Add every local and third-party Django application used by the project.
# Application ordering can affect template overrides and startup behavior.
# Prefer an explicit AppConfig path when the application provides one:
#     "your_app.apps.YourAppConfig",
INSTALLED_APPS = [
    # Application-specific examples:
    # "your_app",
    # "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Optional application display metadata. Define the exact structure consumed
# by the project; this is not a standard Django setting.
# APPS_NAMES = [
#     ["your_app", "Human-readable application name"],
# ]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "relecov_platform.urls"
WSGI_APPLICATION = "relecov_platform.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Add application-owned template directories when needed:
        # "DIRS": [BASE_DIR / "documents" / "service_templates"],
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True

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

# Optional django-crontab configuration. Enable "django_crontab" in
# INSTALLED_APPS before activating these settings.
# LOG_CRONTAB_FILE = BASE_DIR / "logs" / "crontab.log"
# CRONJOBS = [
#     ("*/15 * * * *", "your_app.cron.job", f">>{LOG_CRONTAB_FILE}"),
# ]
# CRONTAB_COMMAND_SUFFIX = "2>&1"

# Optional upload limit in bytes. Django's default is 2.5 MiB.
# DATA_UPLOAD_MAX_MEMORY_SIZE = 10_000_000

# Enable only when every request reaches Django through a trusted proxy that
# overwrites X-Forwarded-Proto. Incorrect use lets clients spoof HTTPS.
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Add application/framework-specific settings below, for example REST framework
# authentication, Swagger, Crispy Forms, logging or cleanup policies.

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
