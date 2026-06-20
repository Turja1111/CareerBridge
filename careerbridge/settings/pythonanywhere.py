"""
CareerBridge — PythonAnywhere Settings

Use this settings module when deploying on PythonAnywhere.
Usage: Set DJANGO_SETTINGS_MODULE=careerbridge.settings.pythonanywhere
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────
#  SECURITY
# ─────────────────────────────────────────────

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-CHANGE-ME-in-production-x9k2m3n4p5q6r7s8t0u",
)

DEBUG = False

ALLOWED_HOSTS = [
    "turja221b.pythonanywhere.com",
    "localhost",
    "127.0.0.1",
]


# ─────────────────────────────────────────────
#  APPLICATION DEFINITION
# ─────────────────────────────────────────────

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "django_filters",
    # Local apps
    "apps.core",
    "apps.jobs",
    "apps.scraper",
    "apps.analytics",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "careerbridge.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "careerbridge.wsgi.application"


# ─────────────────────────────────────────────
#  DATABASE — SQLite (PythonAnywhere free tier)
# ─────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ─────────────────────────────────────────────
#  PASSWORD VALIDATION
# ─────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ─────────────────────────────────────────────
#  INTERNATIONALIZATION
# ─────────────────────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True


# ─────────────────────────────────────────────
#  STATIC FILES
# ─────────────────────────────────────────────

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ─────────────────────────────────────────────
#  REST FRAMEWORK
# ─────────────────────────────────────────────

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}


# ─────────────────────────────────────────────
#  SCRAPER SETTINGS
# ─────────────────────────────────────────────

SCRAPER_MAX_JOBS_PER_SEARCH = int(os.environ.get("SCRAPER_MAX_JOBS_PER_SEARCH", 30))
SCRAPER_MAX_SEARCH_COMBINATIONS = int(os.environ.get("SCRAPER_MAX_SEARCH_COMBINATIONS", 18))
SCRAPER_DAILY_HOUR = int(os.environ.get("SCRAPER_DAILY_HOUR", 8))
SCRAPER_DAILY_MINUTE = int(os.environ.get("SCRAPER_DAILY_MINUTE", 0))
SCRAPER_HEADLESS = True
SCRAPER_REQUEST_DELAY = int(os.environ.get("SCRAPER_REQUEST_DELAY", 2))

# LinkedIn credentials
LINKEDIN_EMAIL = os.environ.get("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.environ.get("LINKEDIN_PASSWORD", "")

# Encryption key
CREDENTIAL_ENCRYPTION_KEY = os.environ.get("CREDENTIAL_ENCRYPTION_KEY", "")


# ─────────────────────────────────────────────
#  CELERY — Disabled (no Redis on PythonAnywhere)
# ─────────────────────────────────────────────

CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"


# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} — {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "apps.scraper": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": True,
        },
    },
}
