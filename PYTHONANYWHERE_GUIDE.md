# CareerBridge — PythonAnywhere Deployment Guide

## Step 1: Clone from GitHub

Use the Bash console, not the Files upload button.

Click "Open Bash console here", then run:

```bash
cd /home/Turja221b
git clone https://github.com/Turja1111/CareerBridge.git
cd CareerBridge
ls
```

After `ls`, you should see:

```
apps/
careerbridge/
static/
templates/
manage.py
requirements.txt
requirements_pythonanywhere.txt
pythonanywhere_task.py
pythonanywhere_wsgi.py
.env.pythonanywhere
```

## Step 2: Create Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.13 careerbridge-env
cd /home/Turja221b/CareerBridge
pip install --upgrade pip
pip install -r requirements_pythonanywhere.txt
```

## Step 3: Install Playwright

```bash
playwright install chromium
playwright install-deps
```

## Step 4: Django Setup

```bash
python manage.py check --settings=careerbridge.settings.pythonanywhere
python manage.py migrate --settings=careerbridge.settings.pythonanywhere
python manage.py collectstatic --no-input --settings=careerbridge.settings.pythonanywhere
python manage.py createsuperuser --settings=careerbridge.settings.pythonanywhere
```

## Step 5: Web Tab Settings

Go to **Web** tab and set:

**Source code:**
```
/home/Turja221b/CareerBridge
```

**Working directory:**
```
/home/Turja221b/CareerBridge
```

**Virtualenv:**
```
/home/Turja221b/.virtualenvs/careerbridge-env
```

**Static files:**
```
/static/    /home/Turja221b/CareerBridge/staticfiles
```

## Step 6: WSGI Configuration File

Go to **Web → WSGI configuration file** and replace with:

```python
import os
import sys

PROJECT_DIR = '/home/Turja221b/CareerBridge'

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.environ['DJANGO_SETTINGS_MODULE'] = 'careerbridge.settings.pythonanywhere'
os.environ['PYTHONANYWHERE_USERNAME'] = 'Turja221b'
os.environ['SECRET_KEY'] = 'django-prod-Turja221b-8fKp2qX9mV7zR4sL1nB6cD3hY0aW5eU'
os.environ['LINKEDIN_EMAIL'] = 'your-email@gmail.com'
os.environ['LINKEDIN_PASSWORD'] = 'your-password'
os.environ['CREDENTIAL_ENCRYPTION_KEY'] = 'your-fernet-key'

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
```

## Step 7: Reload Web App

Click the **Reload** button on the Web tab.

## Step 8: Set Up Scheduled Task (Scraper)

Go to **Tasks** tab and add:

**Command:**
```
/home/Turja221b/.virtualenvs/careerbridge-env/bin/python /home/Turja221b/CareerBridge/pythonanywhere_task.py
```

**Schedule:** Daily at 8:00 AM (or your preferred time)

## Important Notes

### Scraper Limitations on PythonAnywhere

- **Playwright** may not work due to browser restrictions
- **Celery** is not available — use the management command instead
- Consider running the scraper **locally** and only hosting the **web dashboard** on PA

### Database

PythonAnywhere uses **SQLite** by default.
- ArrayField automatically falls back to JSONField (no migration needed)
- For PostgreSQL, use an external service (e.g., Supabase, Railway)

### Manual Scraper Run

To test the scraper manually:
```bash
python manage.py run_scrape --settings=careerbridge.settings.pythonanywhere
```

## Troubleshooting

### 500 Error
- Check error logs in **Web → Error log**
- Ensure all migrations are applied

### Static Files Not Loading
- Run: `python manage.py collectstatic --no-input --settings=careerbridge.settings.pythonanywhere`

### Scraper Not Working
- Check Playwright: `playwright install chromium`
- Test manually: `python manage.py run_scrape --settings=careerbridge.settings.pythonanywhere`
- Check **Tasks → Logs** for scheduled task output
