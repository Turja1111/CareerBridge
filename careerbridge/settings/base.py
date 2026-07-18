"""
CareerBridge — Base Settings
Common settings shared across all environments.
"""

import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())


# ─────────────────────────────────────────────
#  Application Definition
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
    "django_celery_beat",
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
#  Database — PostgreSQL
# ─────────────────────────────────────────────

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="linkedin_job_alert"),
        "USER": config("DB_USER", default="postgres"),
        "PASSWORD": config("DB_PASSWORD", default="Admin"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}


# ─────────────────────────────────────────────
#  Password Validation
# ─────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ─────────────────────────────────────────────
#  Internationalization
# ─────────────────────────────────────────────

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True


# ─────────────────────────────────────────────
#  Static Files
# ─────────────────────────────────────────────

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# ─────────────────────────────────────────────
#  Media Files
# ─────────────────────────────────────────────

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ─────────────────────────────────────────────
#  Default Primary Key
# ─────────────────────────────────────────────

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ─────────────────────────────────────────────
#  Django REST Framework
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
#  Celery Configuration
# ─────────────────────────────────────────────

CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE


# ─────────────────────────────────────────────
#  Scraper Settings
# ─────────────────────────────────────────────

SCRAPER_MAX_JOBS_PER_SEARCH = config("SCRAPER_MAX_JOBS_PER_SEARCH", default=30, cast=int)
SCRAPER_MAX_SEARCH_COMBINATIONS = config("SCRAPER_MAX_SEARCH_COMBINATIONS", default=18, cast=int)
SCRAPER_DAILY_HOUR = config("SCRAPER_DAILY_HOUR", default=8, cast=int)
SCRAPER_DAILY_MINUTE = config("SCRAPER_DAILY_MINUTE", default=0, cast=int)
SCRAPER_HEADLESS = config("SCRAPER_HEADLESS", default=True, cast=bool)
SCRAPER_REQUEST_DELAY = config("SCRAPER_REQUEST_DELAY", default=2, cast=int)

# LinkedIn credentials
LINKEDIN_EMAIL = config("LINKEDIN_EMAIL", default="")
LINKEDIN_PASSWORD = config("LINKEDIN_PASSWORD", default="")

# BDJobs credentials
BDJOBS_EMAIL = config("BDJOBS_EMAIL", default="")
BDJOBS_PASSWORD = config("BDJOBS_PASSWORD", default="")
SCRAPER_ENABLE_BDJOBS = config("SCRAPER_ENABLE_BDJOBS", default=True, cast=bool)

# Encryption key for credential storage
CREDENTIAL_ENCRYPTION_KEY = config("CREDENTIAL_ENCRYPTION_KEY", default="")


# ─────────────────────────────────────────────
#  Logging
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
            "level": "INFO",
            "propagate": True,
        },
    },
}
