"""
CareerBridge — Local Development Settings
"""

from .base import *  # noqa: F401,F403

DEBUG = True

# Use ManifestStaticFilesStorage alternative for dev (no hashing)
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
