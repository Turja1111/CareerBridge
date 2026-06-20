#!/usr/bin/env python
"""
CareerBridge — PythonAnywhere Scheduled Task Script

Set this as your PythonAnywhere "Task" in the Tasks tab:
    /home/Turja221b/.virtualenvs/careerbridge-env/bin/python /home/Turja221b/CareerBridge/pythonanywhere_task.py

Schedule it to run daily (e.g., at 8:00 AM).
"""

import os
import sys
import subprocess
from datetime import date

# ── Setup Django ──────────────────────────────────────
project_home = "/home/Turja221b/CareerBridge"
os.chdir(project_home)
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "careerbridge.settings.pythonanywhere")
os.environ["PYTHONANYWHERE_USERNAME"] = "Turja221b"

import django
django.setup()

# ── Check if scrape already ran today ─────────────────
from apps.scraper.models import ScrapeLog

already_ran = ScrapeLog.objects.filter(
    started_at__date=date.today(),
    status="success",
).exists()

if already_ran:
    print(f"[{date.today()}] Scrape already ran today. Skipping.")
    sys.exit(0)

# ── Run the scraper ───────────────────────────────────
print(f"[{date.today()}] Starting scheduled scrape...")
result = subprocess.run(
    [sys.executable, "manage.py", "run_scrape", "--triggered-by=schedule"],
    capture_output=True,
    text=True,
    cwd=project_home,
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

sys.exit(result.returncode)
