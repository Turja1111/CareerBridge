"""
CareerBridge — PythonAnywhere WSGI Entry Point
"""

import os
import sys

PROJECT_DIR = '/home/Turja221b/CareerBridge'

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'careerbridge.settings.pythonanywhere'
os.environ['PYTHONANYWHERE_USERNAME'] = 'Turja221b'
os.environ['SECRET_KEY'] = 'django-prod-Turja221b-8fKp2qX9mV7zR4sL1nB6cD3hY0aW5eU'

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
