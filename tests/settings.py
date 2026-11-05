from pathlib import Path

SECRET_KEY = "test-only"
DEBUG = False
USE_TZ = True

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_URLCONF = "tests.urls"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django_plotly_dash.apps.DjangoPlotlyDashConfig",
    "rest_framework",
    "tests.apps.CoreTestConfig",
    "tests.apps.DashboardTestConfig",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Keep source-checkout tests independent from the deployment database.
MIGRATION_MODULES = {
    "core": None,
    "dashboard": None,
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = "/tmp/relecov-platform-test-media"
