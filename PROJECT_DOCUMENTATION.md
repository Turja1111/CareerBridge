# 🚀 Project Documentation

---

## 💡 Project Names : CareerBridge
"Turning job chaos into clear direction by matching your skills with real opportunities."

---

# CareerBridge — Complete Project Documentation

> **Version:** 1.0.0
> **Stack:** Django · PostgreSQL · Playwright · Celery · Redis · Chart.js
> **Author:** Personal Project
> **Last Updated:** 2026

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Goals & Vision](#2-goals--vision)
3. [Feature List](#3-feature-list)
4. [System Architecture](#4-system-architecture)
5. [Tech Stack](#5-tech-stack)
6. [Project Structure](#6-project-structure)
7. [Database Schema](#7-database-schema)
8. [Django Apps Breakdown](#8-django-apps-breakdown)
9. [Playwright Scraper Design](#9-playwright-scraper-design)
10. [Celery Task Queue & Scheduler](#10-celery-task-queue--scheduler)
11. [API Endpoints](#11-api-endpoints)
12. [Frontend UI Design](#12-frontend-ui-design)
13. [Analytics Dashboard](#13-analytics-dashboard)
14. [Environment Configuration](#14-environment-configuration)
15. [Installation & Setup](#15-installation--setup)
16. [Security Considerations](#16-security-considerations)
17. [Testing Strategy](#17-testing-strategy)
18. [Deployment Guide](#18-deployment-guide)
19. [Future Roadmap](#19-future-roadmap)
20. [Comparison vs Existing Tools](#20-comparison-vs-existing-tools)
21. [Docker Setup](#21-docker-setup)

---

## 1. Project Overview

**CareerBridge** is a self-hosted, personal job intelligence platform that automatically scrapes LinkedIn job postings based on your saved preferences, stores them in a PostgreSQL database, and displays them in a beautiful, analytics-rich web dashboard built with Django.

Instead of scrolling LinkedIn endlessly and losing track of opportunities, CareerBridge brings everything to a clean personal portal — with smart filters, skill analytics, salary insights, and one-click apply links — all running on your local machine.

---

## 2. Goals & Vision

### Primary Goals
- ✅ Auto-login to LinkedIn and scrape jobs matching your personal preferences
- ✅ Store all job data in a structured PostgreSQL database
- ✅ Present jobs in a beautiful personal dashboard (not LinkedIn's UI)
- ✅ Provide a powerful analytics section with charts and insights
- ✅ Run scraping automatically on a daily schedule with zero manual effort

### Design Philosophy
- **Zero noise** — Only show jobs that match your profile
- **Data-first** — Every job is enriched with parsed skills, salary ranges, and location info
- **Offline-ready** — All data lives on your machine; no third-party service dependency
- **Beautiful by default** — UI should feel like a premium SaaS product, not a personal script

---

## 3. Feature List

### 🔐 Authentication & Setup
- [ ] Django admin-secured dashboard (single user)
- [ ] LinkedIn credential vault (stored encrypted in DB)
- [ ] LinkedIn session persistence (cookies saved, avoids repeated logins)
- [ ] 2FA / CAPTCHA handling mode (headless → headed browser fallback)

### 📥 Scraper Engine
- [ ] Auto-login to LinkedIn using Playwright
- [ ] Scrape user's saved job preferences from LinkedIn profile
- [ ] Collect jobs matching those preferences (title, location, remote type)
- [ ] Extract: job title, company, location, work type, description, date posted, apply URL, salary (if shown), required skills
- [ ] Auto-parse skills from job descriptions using keyword matching
- [ ] Deduplicate jobs (never save the same posting twice)
- [ ] Smart startup: scrape immediately if not done today; skip if already done
- [ ] Daily scheduled scrape via Celery Beat

### 💼 Job Board
- [ ] Full job post view (styled like a premium job board)
- [ ] Filter by: work type (remote/hybrid/on-site), date, company, skill, location
- [ ] Search bar (title, company, keyword)
- [ ] Bookmark / save favourite jobs
- [ ] Mark jobs as Applied / Interested / Ignored
- [ ] One-click "Apply on LinkedIn" button
- [ ] Pagination + infinite scroll option
- [ ] New jobs badge (jobs added in last 24h highlighted)

### 📊 Analytics Dashboard
- [ ] Top in-demand skills (bar chart)
- [ ] Jobs by work type distribution (donut chart)
- [ ] Jobs posted over time (line chart, last 30 days)
- [ ] Salary range analysis (box plot / range chart)
- [ ] Top hiring companies (horizontal bar chart)
- [ ] Location heatmap / top locations list
- [ ] Skills required per job category (grouped bar)
- [ ] New jobs per day counter
- [ ] Average skills per job posting
- [ ] Most common job titles (word cloud or ranked list)

### ⚙️ Settings & Control
- [ ] Manual "Scrape Now" trigger from UI
- [ ] Scraper status panel (running / idle / last run / jobs found today)
- [ ] View scraper logs in UI
- [ ] Configure job search keywords and locations
- [ ] Notification: toast alerts when new jobs arrive

---

## 4. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CareerBridge System                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│   │   Browser    │────▶│  Django App  │────▶│  PostgreSQL  │    │
│   │  (You)       │◀────│  (Port 8000) │◀────│  Database    │    │
│   └──────────────┘     └──────┬───────┘     └──────────────┘    │
│                               │                                   │
│                    ┌──────────▼──────────┐                       │
│                    │    Celery Worker    │                       │
│                    │  (Background Tasks) │                       │
│                    └──────────┬──────────┘                       │
│                               │                                   │
│                    ┌──────────▼──────────┐                       │
│                    │   Celery Beat       │                       │
│                    │  (Daily Scheduler)  │                       │
│                    └──────────┬──────────┘                       │
│                               │                                   │
│                    ┌──────────▼──────────┐                       │
│                    │  Playwright Engine  │                       │
│                    │  (Headless Chrome)  │                       │
│                    └──────────┬──────────┘                       │
│                               │                                   │
│                    ┌──────────▼──────────┐                       │
│                    │    LinkedIn.com     │                       │
│                    │  (Job Posts)        │                       │
│                    └─────────────────────┘                       │
│                                                                   │
│   ┌────────────┐                                                  │
│   │   Redis    │  ← Celery broker + result backend               │
│   └────────────┘                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow
```
LinkedIn ──► Playwright Scraper ──► Celery Task ──► PostgreSQL
                                                         │
                                                    Django ORM
                                                         │
                                               Django Templates
                                                         │
                                              Browser Dashboard
```

---

## 5. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | Django 5.x | Main application, ORM, routing, templating |
| **Database** | PostgreSQL 16 | Persistent job storage |
| **Scraper** | Playwright (Python async) | LinkedIn automation & data extraction |
| **Task Queue** | Celery 5.x | Background scraping tasks |
| **Task Broker** | Redis 7 | Celery message broker |
| **Scheduler** | Celery Beat | Daily automatic scrape |
| **Frontend** | Django Templates + Tailwind CSS | Beautiful responsive UI |
| **Charts** | ApexCharts.js | Interactive analytics |
| **Icons** | Lucide Icons | Clean SVG icons |
| **Fonts** | Syne + DM Mono (Google Fonts) | Distinctive typography |
| **HTTP Client** | Django REST Framework (optional) | Internal API for JS fetch calls |
| **Security** | python-cryptography | Encrypt LinkedIn credentials |
| **Env Config** | python-decouple | `.env` file management |
| **Logging** | Python logging + Django | Scraper and app logs |

---

## 6. Project Structure

```
CareerBridge/
│
├── manage.py
├── requirements.txt
├── .env                        ← Your credentials (never commit)
├── .env.example
├── .gitignore
├── README.md
│
├── CareerBridge/                    ← Django project config
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py             ← Common settings
│   │   ├── local.py            ← Local dev settings
│   │   └── production.py       ← Production settings
│   ├── urls.py
│   ├── celery.py               ← Celery app config
│   └── wsgi.py
│
├── apps/
│   │
│   ├── core/                   ← Base models, mixins, utilities
│   │   ├── models.py
│   │   └── utils.py
│   │
│   ├── scraper/                ← Playwright scraper engine
│   │   ├── models.py           ← ScrapeLog, LinkedInCredential
│   │   ├── playwright_engine.py← Main Playwright logic
│   │   ├── parser.py           ← HTML parsing, skill extraction
│   │   ├── tasks.py            ← Celery tasks
│   │   ├── scheduler.py        ← Smart startup scrape logic
│   │   └── session_manager.py  ← Save/load browser session
│   │
│   ├── jobs/                   ← Job posts app
│   │   ├── models.py           ← JobPost, Company, Skill, etc.
│   │   ├── views.py            ← Job listing, detail, filters
│   │   ├── urls.py
│   │   ├── serializers.py      ← DRF serializers for API
│   │   └── filters.py          ← Django-filter config
│   │
│   ├── analytics/              ← Analytics & charts app
│   │   ├── models.py
│   │   ├── views.py            ← Chart data API endpoints
│   │   ├── urls.py
│   │   └── aggregators.py      ← Query aggregation logic
│   │
│   └── dashboard/              ← Main dashboard shell
│       ├── views.py
│       └── urls.py
│
├── templates/
│   ├── base.html               ← Main layout (navbar, sidebar)
│   ├── dashboard/
│   │   └── index.html          ← Home dashboard
│   ├── jobs/
│   │   ├── list.html           ← Job board
│   │   └── detail.html         ← Single job post
│   ├── analytics/
│   │   └── index.html          ← Analytics dashboard
│   └── scraper/
│       └── status.html         ← Scraper control panel
│
├── static/
│   ├── css/
│   │   ├── main.css            ← Compiled Tailwind / custom CSS
│   │   └── animations.css
│   ├── js/
│   │   ├── charts.js           ← ApexCharts configs
│   │   ├── jobs.js             ← Job board interactions
│   │   └── scraper.js          ← Scraper status polling
│   └── img/
│
└── linkedin_session/           ← Playwright saved session (gitignored)
    └── session.json
```

---

## 7. Database Schema

### Entity Relationship Overview

```
Company ──< JobPost >── Skill
               │
               ├── ScrapeLog
               └── UserJobStatus

LinkedInCredential (1)
UserPreference ──< PreferenceKeyword
```

---

### Table: `jobs_company`

```sql
CREATE TABLE jobs_company (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    linkedin_id     VARCHAR(100) UNIQUE,
    logo_url        TEXT,
    website         TEXT,
    industry        VARCHAR(255),
    created_at      TIMESTAMP DEFAULT NOW()
);
```

---

### Table: `jobs_skill`

```sql
CREATE TABLE jobs_skill (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,  -- e.g. "Python", "Docker"
    category    VARCHAR(100),                   -- e.g. "Programming", "DevOps"
    created_at  TIMESTAMP DEFAULT NOW()
);
```

---

### Table: `jobs_jobpost` *(Core Table)*

```sql
CREATE TABLE jobs_jobpost (
    id              SERIAL PRIMARY KEY,
    linkedin_job_id VARCHAR(50) UNIQUE NOT NULL,
    title           VARCHAR(255) NOT NULL,
    company_id      INTEGER REFERENCES jobs_company(id),
    location        VARCHAR(255),
    work_type       VARCHAR(20),        -- Remote / Hybrid / On-site
    description     TEXT,
    salary_min      INTEGER,            -- Parsed salary range (if available)
    salary_max      INTEGER,
    salary_currency VARCHAR(10),
    experience_level VARCHAR(50),       -- Entry / Mid / Senior
    date_posted     DATE,
    apply_url       TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    scraped_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

---

### Table: `jobs_jobskill` *(Many-to-Many)*

```sql
CREATE TABLE jobs_jobskill (
    id          SERIAL PRIMARY KEY,
    job_id      INTEGER REFERENCES jobs_jobpost(id) ON DELETE CASCADE,
    skill_id    INTEGER REFERENCES jobs_skill(id) ON DELETE CASCADE,
    UNIQUE(job_id, skill_id)
);
```

---

### Table: `jobs_userjobstatus`

```sql
CREATE TABLE jobs_userjobstatus (
    id          SERIAL PRIMARY KEY,
    job_id      INTEGER REFERENCES jobs_jobpost(id) ON DELETE CASCADE,
    status      VARCHAR(20) DEFAULT 'new',  -- new / saved / applied / ignored
    notes       TEXT,
    updated_at  TIMESTAMP DEFAULT NOW()
);
```

---

### Table: `scraper_linkedincredential`

```sql
CREATE TABLE scraper_linkedincredential (
    id                  SERIAL PRIMARY KEY,
    email               VARCHAR(255) NOT NULL,
    encrypted_password  TEXT NOT NULL,          -- AES encrypted
    session_data        TEXT,                   -- JSON browser cookies
    last_login          TIMESTAMP,
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);
```

---

### Table: `scraper_scrapelog`

```sql
CREATE TABLE scraper_scrapelog (
    id              SERIAL PRIMARY KEY,
    started_at      TIMESTAMP DEFAULT NOW(),
    finished_at     TIMESTAMP,
    status          VARCHAR(20),    -- running / success / failed
    jobs_found      INTEGER DEFAULT 0,
    jobs_new        INTEGER DEFAULT 0,
    error_message   TEXT,
    triggered_by    VARCHAR(20)     -- schedule / manual / startup
);
```

---

### Table: `scraper_userpreference`

```sql
CREATE TABLE scraper_userpreference (
    id              SERIAL PRIMARY KEY,
    keywords        TEXT[],         -- PostgreSQL array: ["Python", "Django"]
    locations       TEXT[],         -- ["Remote", "Dhaka", "Bangladesh"]
    work_types      TEXT[],         -- ["Remote", "Hybrid"]
    experience_level VARCHAR(50),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 8. Django Apps Breakdown

### `apps/scraper/playwright_engine.py`

Core responsibilities:
- `login(page)` — Fill credentials, submit, handle 2FA fallback
- `is_logged_in(page)` — Check if session is still valid
- `fetch_user_preferences(page)` → Returns `{ keywords, locations }`
- `search_jobs(page, keyword, location)` → Returns list of raw job dicts
- `extract_job_detail(page, card)` → Extracts all fields from a single card
- `save_session(context)` / `load_session(playwright)` — Cookie persistence

---

### `apps/scraper/parser.py`

Core responsibilities:
- `extract_skills_from_text(description)` — Keyword match against a master skills list
- `parse_salary(text)` → `{ min, max, currency }`
- `parse_experience_level(text)` → `"Entry" | "Mid" | "Senior"`
- `parse_work_type(location_text)` → `"Remote" | "Hybrid" | "On-site"`

**Skill Keywords Database (sample)**
```python
SKILL_KEYWORDS = {
    "Python": ["python", "django", "flask", "fastapi"],
    "JavaScript": ["javascript", "js", "node.js", "react", "vue"],
    "Machine Learning": ["ml", "machine learning", "tensorflow", "pytorch", "sklearn"],
    "SQL": ["sql", "postgresql", "mysql", "database"],
    "Docker": ["docker", "container", "kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    # ... 100+ skills
}
```

---

### `apps/scraper/tasks.py` (Celery)

```python
@shared_task(bind=True, name="scraper.run_scrape")
def run_scrape_task(self, triggered_by="schedule"):
    """
    Main Celery task. Runs Playwright scraper and saves results to PostgreSQL.
    - Creates ScrapeLog entry
    - Calls playwright_engine.run()
    - Updates log with results
    - Handles errors gracefully
    """

@shared_task(name="scraper.startup_check")
def startup_scrape_if_needed():
    """
    Called on Django app startup.
    Checks if scrape already ran today. If not, triggers run_scrape_task.
    """
```

---

### `apps/jobs/models.py`

```python
class JobPost(models.Model):
    WORK_TYPE_CHOICES = [
        ("Remote", "Remote"),
        ("Hybrid", "Hybrid"),
        ("On-site", "On-site"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("saved", "Saved"),
        ("applied", "Applied"),
        ("ignored", "Ignored"),
    ]

    linkedin_job_id = models.CharField(max_length=50, unique=True)
    title           = models.CharField(max_length=255)
    company         = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True)
    location        = models.CharField(max_length=255, blank=True)
    work_type       = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES)
    description     = models.TextField(blank=True)
    salary_min      = models.IntegerField(null=True, blank=True)
    salary_max      = models.IntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True)
    experience_level= models.CharField(max_length=50, blank=True)
    date_posted     = models.DateField(null=True)
    apply_url       = models.URLField(max_length=1000)
    skills          = models.ManyToManyField(Skill, through="JobSkill", blank=True)
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    is_active       = models.BooleanField(default=True)
    scraped_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scraped_at"]
        indexes = [
            models.Index(fields=["date_posted"]),
            models.Index(fields=["work_type"]),
            models.Index(fields=["status"]),
        ]
```

---

### `apps/analytics/aggregators.py`

```python
def top_skills(limit=15):
    """Returns skills ranked by frequency across all job posts."""

def jobs_over_time(days=30):
    """Returns daily job count for the last N days."""

def salary_ranges_by_title():
    """Returns avg/min/max salary grouped by job title."""

def work_type_distribution():
    """Returns count per work type (Remote/Hybrid/On-site)."""

def top_companies(limit=10):
    """Returns companies with the most active postings."""

def skills_by_experience_level():
    """Returns which skills appear most for each experience level."""

def top_locations(limit=10):
    """Returns most common job locations."""
```

---

## 9. Playwright Scraper Design

### Login Flow

```
START
  │
  ▼
Load saved session (linkedin_session/session.json)
  │
  ▼
Navigate to linkedin.com/feed
  │
  ├── Still logged in? ──► YES ──► Go to job search
  │
  └── NO
        │
        ▼
      Navigate to linkedin.com/login
        │
        ▼
      Fill email + password → Submit
        │
        ├── Success (redirected to /feed) ──► Save new session ──► Go to job search
        │
        └── 2FA / CAPTCHA detected
              │
              ▼
            Switch to HEADED mode (visible browser window)
              │
              ▼
            Wait for user to complete manually (60 second timeout)
              │
              ▼
            Save session ──► Go to job search
```

---

### Job Scraping Flow

```
For each (keyword, location) in UserPreference:
  │
  ▼
Build LinkedIn Jobs URL with filters:
  - keywords=Python+Developer
  - location=Remote
  - f_TPR=r86400  (posted in last 24h)
  - sortBy=DD     (newest first)
  │
  ▼
Navigate to search results page
  │
  ▼
Scroll 3–5 times to load all cards
  │
  ▼
For each job card:
  │
  ├── Extract: title, company, location, date, apply_url
  │
  ├── Click card → wait for detail panel
  │
  ├── Extract: full description, salary (if shown)
  │
  ├── Run parser.extract_skills_from_text(description)
  │
  ├── Check DB: does linkedin_job_id already exist?
  │   ├── YES → skip (deduplicate)
  │   └── NO  → save to PostgreSQL
  │
  └── Sleep 1–2 seconds (rate limiting)
```

---

### Session Persistence Strategy

```python
SESSION_FILE = "linkedin_session/session.json"

# After login:
storage_state = await context.storage_state()
# Stores cookies + localStorage → avoids re-login for weeks

# On next startup:
context = await browser.new_context(storage_state=SESSION_FILE)
# LinkedIn thinks it's the same browser session
```

---

## 10. Celery Task Queue & Scheduler

### `CareerBridge/celery.py`

```python
from celery import Celery
from celery.schedules import crontab

app = Celery("CareerBridge")

app.conf.beat_schedule = {
    "daily-linkedin-scrape": {
        "task": "scraper.run_scrape",
        "schedule": crontab(hour=8, minute=0),  # Every day at 08:00
        "kwargs": {"triggered_by": "schedule"},
    },
}
```

### Smart Startup Check

In `apps/scraper/apps.py` (Django AppConfig `ready()` hook):

```python
def ready(self):
    from .scheduler import startup_scrape_check
    startup_scrape_check()
```

In `scheduler.py`:

```python
def startup_scrape_check():
    from .models import ScrapeLog
    from .tasks import run_scrape_task
    from datetime import date

    already_ran = ScrapeLog.objects.filter(
        started_at__date=date.today(),
        status="success"
    ).exists()

    if not already_ran:
        run_scrape_task.delay(triggered_by="startup")
```

### Running All Services

```bash
# Terminal 1 — Django dev server
python manage.py runserver

# Terminal 2 — Celery worker
celery -A CareerBridge worker -l info

# Terminal 3 — Celery Beat scheduler
celery -A CareerBridge beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

---

## 11. API Endpoints

### Jobs API

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/jobs/` | List all jobs (filterable) |
| `GET` | `/api/jobs/<id>/` | Single job detail |
| `PATCH` | `/api/jobs/<id>/status/` | Update job status (saved/applied/ignored) |
| `GET` | `/api/jobs/new/` | Jobs added in last 24h |

**Query Parameters for `/api/jobs/`:**
```
?search=python
?work_type=Remote
?skill=Django
?company=Google
?status=new
?date_from=2026-06-01
?page=2
```

---

### Analytics API

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/api/analytics/top-skills/` | Top 15 in-demand skills |
| `GET` | `/api/analytics/jobs-over-time/` | Daily job counts (30 days) |
| `GET` | `/api/analytics/work-type-distribution/` | Remote/Hybrid/Onsite split |
| `GET` | `/api/analytics/salary-ranges/` | Salary data by job title |
| `GET` | `/api/analytics/top-companies/` | Most active hiring companies |
| `GET` | `/api/analytics/top-locations/` | Top job locations |
| `GET` | `/api/analytics/skills-by-experience/` | Skills per experience level |

---

### Scraper API

| Method | URL | Description |
|--------|-----|-------------|
| `POST` | `/api/scraper/trigger/` | Manually start a scrape |
| `GET` | `/api/scraper/status/` | Current scraper status |
| `GET` | `/api/scraper/logs/` | Last 20 scrape log entries |

---

## 12. Frontend UI Design

### Design System

```css
/* Color Palette */
--bg-primary:   #0d0d14    /* Deep dark navy */
--bg-surface:   #13131f    /* Card backgrounds */
--bg-elevated:  #1c1c2e    /* Elevated cards */
--border:       #2a2a40    /* Subtle borders */
--accent-green: #00d4a0    /* Primary action (Remote badge, CTA) */
--accent-purple:#7c6ff7    /* Secondary action (Hybrid, links) */
--accent-amber: #f5a623    /* Warning / On-site badge */
--text-primary: #e8e8f5    /* Main text */
--text-muted:   #6b6b8a    /* Secondary text */

/* Typography */
--font-display: 'Syne', sans-serif       /* Headers, titles */
--font-body:    'DM Sans', sans-serif    /* Body text */
--font-mono:    'DM Mono', monospace     /* Code, IDs, badges */
```

---

### Page: Job Board (`/jobs/`)

```
┌─────────────────────────────────────────────────────────────────┐
│  NAVBAR: [CareerBridge logo]  [Jobs] [Analytics] [Settings]  [●Live] │
├──────────────┬──────────────────────────────────────────────────┤
│              │  🔍 Search jobs, companies, skills…              │
│   SIDEBAR    ├──────────────────────────────────────────────────┤
│              │  Filters: [All] [Remote] [Hybrid] [On-site]      │
│  📋 All Jobs │  Sort: [Newest] [Relevance]       24 new today ✨ │
│  ⭐ Saved    ├──────────────────────────────────────────────────┤
│  ✅ Applied  │                                                    │
│  🙈 Ignored  │  ┌─────────────────────┐  ┌─────────────────────┐│
│              │  │ 🏢 Bdjobs.com       │  │ 🏢 Google           ││
│  SKILLS      │  │                     │  │                     ││
│  ──────────  │  │ AI Engineer Trainee │  │ Backend Engineer    ││
│  ○ Python    │  │ Talent Centric Ltd. │  │                     ││
│  ○ Django    │  │ 📍 Dhaka  🏠 Remote │  │ 📍 Remote  🌐 Hybrid││
│  ○ React     │  │                     │  │                     ││
│  ○ Docker    │  │ Python · ML · AI    │  │ Go · K8s · AWS      ││
│              │  │                     │  │                     ││
│  COMPANIES   │  │ 🗓 2 days ago       │  │ 🗓 Today           ││
│  ──────────  │  │        [Apply →]    │  │        [Apply →]    ││
│  ○ Bdjobs    │  └─────────────────────┘  └─────────────────────┘│
│  ○ Google    │                                                    │
│  ○ Meta      │  ┌─────────────────────┐  ┌─────────────────────┐│
│              │  │ ...                 │  │ ...                 ││
│              │  └─────────────────────┘  └─────────────────────┘│
└──────────────┴──────────────────────────────────────────────────┘
```

---

### Page: Job Detail (`/jobs/<id>/`)

```
┌────────────────────────────────────────────────────────────────┐
│  ← Back to Jobs                                  [⭐ Save] [✓ Applied] │
├────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [Company Logo]  AI Engineer Trainee               🟢 REMOTE   │
│                  Talent Centric Limited                          │
│                  📍 Dhaka, Bangladesh  •  🗓 Posted 2 days ago │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Required Skills:                                                │
│  [Python] [Machine Learning] [TensorFlow] [PyTorch] [SQL] [AI]  │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  About the Job                                                   │
│  ─────────────                                                   │
│  Talent Centric Limited is looking for AI Engineer Trainee...   │
│                                                                  │
│  Key Responsibilities:                                           │
│  • Assist in developing, testing AI/ML models…                 │
│  • Research and explore new AI technologies…                   │
│  • Work with datasets for data cleaning…                       │
│  ...                                                             │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  [🔗 Apply on LinkedIn]          [Mark as Applied]              │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## 13. Analytics Dashboard

### Page: Analytics (`/analytics/`)

#### Charts Implemented

**1. Top In-Demand Skills** — Horizontal Bar Chart
```
Python     ████████████████████  48 jobs
SQL        ████████████████      38 jobs
Docker     ██████████████        32 jobs
React      ████████████          28 jobs
AWS        ██████████            24 jobs
```

**2. Jobs Posted Over Time** — Line/Area Chart
```
Jobs
 30 │         ╭──╮
 25 │       ╭─╯  ╰──╮
 20 │    ╭──╯        ╰─╮
 15 │────╯              ╰─────
    └────────────────────────▶ Date
     Jun1   Jun7   Jun14  Jun21
```

**3. Work Type Distribution** — Donut Chart
```
        ╭───────╮
       ╱ Remote  ╲     ● Remote   52%
      │   52%     │    ● Hybrid   31%
       ╲  Hybrid ╱     ● On-site  17%
        ╰───────╯
```

**4. Salary Ranges by Job Title** — Range Bar Chart
```
Senior Dev   |────[====]────|   $3000–$8000
Mid Dev      |──[====]──|       $1500–$4000
Junior Dev   |[===]|             $500–$1500
```

**5. Top Hiring Companies** — Ranked Cards
```
🥇 Bdjobs.com          ██████  42 posts
🥈 Brain Station 23    █████   35 posts
🥉 BJIT Group          ████    28 posts
```

**6. Skills per Experience Level** — Grouped Bar Chart
```
Entry: Python > SQL > Git
Mid:   Python > Django > Docker > AWS
Senior: System Design > AWS > K8s > Architecture
```

**7. Top Locations** — Ranked List with counts
```
1. Remote (Worldwide)     — 124 jobs
2. Dhaka, Bangladesh      — 89 jobs
3. Hybrid (Dhaka)         — 43 jobs
```

**8. Summary KPI Cards (top of dashboard)**
```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   247        │ │   18         │ │   63         │ │  Python      │
│   Total Jobs │ │   New Today  │ │   Companies  │ │  Top Skill   │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

---

## 14. Environment Configuration

### `.env` file

```properties
# Django
SECRET_KEY=your-very-secret-django-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=linkedin_job_alert
DB_USER=postgres
DB_PASSWORD=Admin
DB_HOST=localhost
DB_PORT=5432

# Redis (Celery broker)
REDIS_URL=redis://localhost:6379/0

# LinkedIn Credentials
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword

# Encryption key for storing credentials in DB
CREDENTIAL_ENCRYPTION_KEY=generate-with-fernet-keygen

# Scraper Settings
SCRAPER_MAX_JOBS_PER_SEARCH=30
SCRAPER_DAILY_HOUR=8
SCRAPER_DAILY_MINUTE=0
SCRAPER_HEADLESS=True
SCRAPER_REQUEST_DELAY=2
```

### `CareerBridge/settings/base.py` (Database section)

```python
import os
from decouple import config

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     config("DB_NAME"),
        "USER":     config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST":     config("DB_HOST", default="localhost"),
        "PORT":     config("DB_PORT", default="5432"),
    }
}

CELERY_BROKER_URL         = config("REDIS_URL")
CELERY_RESULT_BACKEND     = config("REDIS_URL")
CELERY_ACCEPT_CONTENT     = ["json"]
CELERY_TASK_SERIALIZER    = "json"
CELERY_RESULT_SERIALIZER  = "json"
```

---

## 15. Installation & Setup

### Prerequisites

```
✅ Python 3.11+
✅ PostgreSQL 15+
✅ Redis 7+
✅ pip / virtualenv
```

### Step 1 — Clone & Virtual Environment

```bash
git clone https://github.com/yourusername/CareerBridge.git
cd CareerBridge
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 3 — Configure Environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL and LinkedIn credentials
```

### Step 4 — Create PostgreSQL Database

```bash
psql -U postgres
CREATE DATABASE linkedin_job_alert;
\q
```

### Step 5 — Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser    # optional, for /admin
```

### Step 6 — Start Redis

```bash
# Linux/Mac
redis-server

# Windows (WSL or Redis for Windows)
redis-server.exe
```

### Step 7 — Start Everything

```bash
# Terminal 1 — Django
python manage.py runserver

# Terminal 2 — Celery Worker
celery -A CareerBridge worker -l info

# Terminal 3 — Celery Beat
celery -A CareerBridge beat -l info

# Open browser
http://localhost:8000
```

### `requirements.txt`

```
Django>=5.0
djangorestframework>=3.15
django-filter>=23.5
django-celery-beat>=2.6
celery>=5.3
redis>=5.0
psycopg2-binary>=2.9
playwright>=1.44
python-decouple>=3.8
cryptography>=42.0
Pillow>=10.0
whitenoise>=6.6          # Static file serving
```

---

## 16. Security Considerations

| Risk | Mitigation |
|------|-----------|
| LinkedIn credentials in plain text | AES-encrypted using `cryptography.fernet` before DB storage |
| Session cookies exposed | `linkedin_session/` folder in `.gitignore`; file permissions 600 |
| Django SECRET_KEY exposed | Loaded from `.env`, never hardcoded |
| SQL injection | Django ORM used exclusively; no raw SQL with user input |
| XSS in job descriptions | Django templates auto-escape; descriptions rendered as plain text |
| CSRF attacks | Django CSRF middleware enabled on all POST endpoints |
| Brute force on /admin | Use strong superuser password; optionally add `django-axes` |
| `.env` committed to git | `.gitignore` includes `.env`, `jobs.db`, `*.json` session files |

### Credential Encryption Example

```python
from cryptography.fernet import Fernet

ENCRYPTION_KEY = config("CREDENTIAL_ENCRYPTION_KEY").encode()
fernet = Fernet(ENCRYPTION_KEY)

# Encrypt before saving
encrypted = fernet.encrypt(password.encode()).decode()

# Decrypt before use
password = fernet.decrypt(encrypted.encode()).decode()
```

---

## 17. Testing Strategy

### Test Coverage Targets

| Module | Test Type | Coverage Goal |
|--------|-----------|--------------|
| `jobs/models.py` | Unit | 90% |
| `scraper/parser.py` | Unit | 95% |
| `analytics/aggregators.py` | Unit | 85% |
| `jobs/views.py` | Integration | 80% |
| `analytics/views.py` | Integration | 75% |
| `scraper/playwright_engine.py` | E2E (mocked) | 60% |

### Sample Test

```python
# tests/test_parser.py
from apps.scraper.parser import extract_skills_from_text

def test_extract_python_django():
    text = "We need Python developers with Django and PostgreSQL experience."
    skills = extract_skills_from_text(text)
    assert "Python" in skills
    assert "Django" in skills
    assert "SQL" in skills

def test_parse_salary():
    from apps.scraper.parser import parse_salary
    result = parse_salary("Salary: $3,000 - $5,000 per month")
    assert result["min"] == 3000
    assert result["max"] == 5000
```

---

## 18. Deployment Guide

> For personal use, localhost is perfectly fine. But if you want to access your dashboard from anywhere:

### Option A — Local Network Access
```bash
python manage.py runserver 0.0.0.0:8000
# Access from any device on your WiFi: http://YOUR_PC_IP:8000
```

### Option B — VPS (DigitalOcean / Vultr / Hetzner ~$5/month)

```
VPS Setup:
1. Ubuntu 24.04
2. Install PostgreSQL, Redis, Python
3. Clone repo, setup .env
4. Use Gunicorn as WSGI server
5. Nginx as reverse proxy
6. Optional: Cloudflare Tunnel for HTTPS without domain
```

```bash
# Gunicorn
gunicorn CareerBridge.wsgi:application --workers 2 --bind 0.0.0.0:8000

# Celery as systemd services
# (create /etc/systemd/system/CareerBridge-worker.service)
```

### Option C — Docker Compose (Cleanest)

> See [Section 21: Docker Setup](#21-docker-setup) for the complete Dockerfile, `docker-compose.yml`, `.dockerignore`, environment configuration, build/run instructions, and production tips.

---

## 19. Future Roadmap

### v1.1 — Enhanced Scraping
- [ ] Scrape job recommendations from LinkedIn homepage
- [ ] Detect and handle LinkedIn rate limiting (exponential backoff)
- [ ] Scrape company info (size, industry) automatically
- [ ] Support multiple LinkedIn accounts

### v1.2 — AI-Powered Features
- [ ] Auto-match your skills vs job requirements (gap analysis)
- [ ] GPT-powered "Why you're a good fit" summary per job
- [ ] Auto-generate tailored cover letter drafts
- [ ] Skill gap radar: "You're missing Docker for 40% of your target jobs"

### v1.3 — Notifications
- [ ] Email digest of new jobs every morning
- [ ] Telegram bot notifications for high-match jobs
- [ ] Browser push notifications

### v1.4 — Export & Reports
- [ ] Export jobs to Excel / CSV
- [ ] Weekly PDF report of job market trends
- [ ] Application tracker with timeline

### v1.5 — Mobile
- [ ] Progressive Web App (PWA) support
- [ ] Mobile-optimized responsive layout
- [ ] Swipe to save / ignore jobs (Tinder-style)

---

## 20. Comparison vs Existing Tools

| Feature | LinkedIn (native) | Job boards | CareerBridge |
|---------|------------------|-----------|---------|
| Personal job feed | ✅ | ❌ | ✅ |
| Custom beautiful UI | ❌ | Partial | ✅ |
| Persistent job history | ❌ (disappears) | ❌ | ✅ (forever in DB) |
| Skill analytics | ❌ | ❌ | ✅ |
| Salary analysis | Limited | Limited | ✅ |
| No ads / distractions | ❌ | ❌ | ✅ |
| Apply status tracking | ❌ | Limited | ✅ |
| Data ownership | ❌ (LinkedIn owns it) | ❌ | ✅ (your DB) |
| Works offline (cached) | ❌ | ❌ | ✅ |
| Fully customizable | ❌ | ❌ | ✅ |
| Free forever | ❌ (Premium) | Partial | ✅ |
| Auto-scrape on schedule | N/A | N/A | ✅ |

---

## 21. Docker Setup

This section provides everything needed to run CareerBridge entirely inside Docker containers — no local Python, PostgreSQL, or Redis installation required.

> **Why Docker?** Docker guarantees identical environments across machines, eliminates "works on my machine" bugs, and makes the full stack (Django + PostgreSQL + Redis + Celery + Playwright) a single `docker compose up` command.

---

### 21.1 Prerequisites

```
✅ Docker Engine 24+      (or Docker Desktop on Windows/Mac)
✅ Docker Compose v2+     (bundled with Docker Desktop)
```

Verify your installation:
```bash
docker --version          # Docker version 27.x
docker compose version    # Docker Compose version v2.x
```

---

### 21.2 Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
# ============================================================
#  CareerBridge — Multi-stage Dockerfile
# ============================================================

# ---------- Stage 1: Base image with system deps ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        # Playwright system dependencies
        libnss3 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libxkbcommon0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        libwayland-client0 \
    && rm -rf /var/lib/apt/lists/*


# ---------- Stage 2: Python dependencies ----------
FROM base AS deps

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser
RUN playwright install chromium


# ---------- Stage 3: Application ----------
FROM deps AS app

WORKDIR /app

COPY . .

# Collect static files (uses whitenoise for serving)
RUN python manage.py collectstatic --noinput --settings=CareerBridge.settings.production 2>/dev/null || true

# Default command — overridden per service in docker-compose
CMD ["gunicorn", "CareerBridge.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]

EXPOSE 8000
```

---

### 21.3 .dockerignore

Create a `.dockerignore` file to keep images small and avoid leaking secrets:

```dockerignore
# Version control
.git
.gitignore

# Environment & secrets
.env
.env.*
!.env.example

# Python
__pycache__/
*.pyc
*.pyo
venv/
.venv/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Docker
Dockerfile
docker-compose*.yml
.dockerignore

# Playwright saved sessions (sensitive)
linkedin_session/

# Docs & misc
*.md
LICENSE
```

---

### 21.4 docker-compose.yml (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  # ─────────────── PostgreSQL ───────────────
  db:
    image: postgres:16-alpine
    container_name: CareerBridge-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME:-linkedin_job_alert}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-Admin}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres} -d ${DB_NAME:-linkedin_job_alert}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─────────────── Redis ───────────────
  redis:
    image: redis:7-alpine
    container_name: CareerBridge-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # ─────────────── Django Web Server ───────────────
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: CareerBridge-web
    restart: unless-stopped
    command: python manage.py runserver 0.0.0.0:8000
    ports:
      - "8000:8000"
    env_file: .env
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app                          # Live reload in dev
      - playwright_sessions:/app/linkedin_session
      - static_files:/app/staticfiles
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ─────────────── Celery Worker ───────────────
  worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: CareerBridge-worker
    restart: unless-stopped
    command: celery -A CareerBridge worker -l info --concurrency=2
    env_file: .env
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
      - playwright_sessions:/app/linkedin_session
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  # ─────────────── Celery Beat Scheduler ───────────────
  beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: CareerBridge-beat
    restart: unless-stopped
    command: celery -A CareerBridge beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    env_file: .env
    environment:
      - DB_HOST=db
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - .:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

volumes:
  postgres_data:       # Persistent DB data across restarts
  redis_data:          # Redis persistence (optional AOF/RDB)
  playwright_sessions: # LinkedIn browser session cookies
  static_files:        # Django collectstatic output
```

---

### 21.5 Docker Environment Variables

The `docker-compose.yml` reads from your `.env` file. Ensure these values are set (note `DB_HOST` is overridden to `db` inside containers):

```properties
# .env (Docker-aware)

# Django
SECRET_KEY=your-very-secret-django-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# PostgreSQL — container hostname is "db" (set via docker-compose env override)
DB_NAME=linkedin_job_alert
DB_USER=postgres
DB_PASSWORD=Admin
DB_HOST=localhost        # Overridden to "db" inside containers
DB_PORT=5432

# Redis — container hostname is "redis" (set via docker-compose env override)
REDIS_URL=redis://localhost:6379/0   # Overridden inside containers

# LinkedIn Credentials
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword

# Encryption key
CREDENTIAL_ENCRYPTION_KEY=generate-with-fernet-keygen

# Scraper Settings
SCRAPER_MAX_JOBS_PER_SEARCH=30
SCRAPER_DAILY_HOUR=8
SCRAPER_DAILY_MINUTE=0
SCRAPER_HEADLESS=True
SCRAPER_REQUEST_DELAY=2
```

> **Note:** `DB_HOST` and `REDIS_URL` are overridden inside Docker via the `environment` block in `docker-compose.yml`, so you don't need to change your `.env` when switching between local and Docker development.

---

### 21.6 Build & Run

#### First-Time Setup

```bash
# 1. Build all images
docker compose build

# 2. Start services (detached mode)
docker compose up -d

# 3. Run database migrations
docker compose exec web python manage.py migrate

# 4. Create Django superuser (optional, for /admin)
docker compose exec web python manage.py createsuperuser

# 5. Open in browser
# → http://localhost:8000
```

#### Daily Usage

```bash
# Start everything
docker compose up -d

# View live logs (all services)
docker compose logs -f

# View logs for a specific service
docker compose logs -f web
docker compose logs -f worker

# Stop everything (data is preserved in volumes)
docker compose down

# Stop AND delete all data (database, sessions, etc.)
docker compose down -v
```

#### Common Operations

```bash
# Run Django management commands
docker compose exec web python manage.py shell
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Manually trigger a scrape
docker compose exec web python manage.py shell -c "
from apps.scraper.tasks import run_scrape_task
run_scrape_task.delay(triggered_by='manual')
"

# Access PostgreSQL directly
docker compose exec db psql -U postgres -d linkedin_job_alert

# Access Redis CLI
docker compose exec redis redis-cli

# Rebuild after requirements.txt changes
docker compose build --no-cache web
docker compose up -d

# Check service health
docker compose ps
```

---

### 21.7 docker-compose.prod.yml (Production Override)

For production deployment, create a separate override file:

```yaml
# docker-compose.prod.yml
version: "3.9"

services:
  web:
    command: gunicorn CareerBridge.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
    environment:
      - DEBUG=False
      - DJANGO_SETTINGS_MODULE=CareerBridge.settings.production
    volumes: []   # Don't mount source code in production
    # Remove port exposure if behind Nginx
    # ports: []

  worker:
    command: celery -A CareerBridge worker -l warning --concurrency=4
    environment:
      - DJANGO_SETTINGS_MODULE=CareerBridge.settings.production
    volumes: []

  beat:
    command: celery -A CareerBridge beat -l warning --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DJANGO_SETTINGS_MODULE=CareerBridge.settings.production
    volumes: []

  # ─────────────── Nginx Reverse Proxy ───────────────
  nginx:
    image: nginx:1.27-alpine
    container_name: CareerBridge-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_files:/app/staticfiles:ro
    depends_on:
      - web

volumes:
  static_files:
```

Run with production overrides:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

### 21.8 Playwright in Docker — Important Notes

| Consideration | Details |
|----------|----------|
| **Browser installation** | The `Dockerfile` runs `playwright install chromium` to download the browser binary inside the image. |
| **Headless-only** | Docker containers have no display server. The scraper **must** run with `SCRAPER_HEADLESS=True`. |
| **2FA / CAPTCHA fallback** | The headed-mode fallback (visible browser for manual 2FA) won't work inside Docker. Pre-authenticate on your host machine and copy `linkedin_session/session.json` into the `playwright_sessions` volume. |
| **Session sharing** | The `playwright_sessions` volume is shared between `web` and `worker` services so session cookies persist. |
| **Memory** | Chromium inside Docker can be memory-hungry. Allocate at least **1 GB RAM** to Docker (2 GB recommended). |

#### Pre-authenticate LinkedIn Session (for Docker)

```bash
# On your host machine (with Playwright installed locally):
cd CareerBridge
python -c "
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Visible browser
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto('https://www.linkedin.com/login')
        input('Log in manually, handle 2FA, then press Enter here...')
        await context.storage_state(path='linkedin_session/session.json')
        await browser.close()

asyncio.run(main())
"

# The session.json is now saved. Docker's volume will pick it up.
```

---

### 21.9 Volume Management

| Volume | Purpose | Safe to delete? |
|--------|---------|----------------|
| `postgres_data` | All scraped jobs, companies, skills, user preferences | ❌ **No** — this is your database |
| `redis_data` | Celery task queue state and results | ✅ Yes — recreated automatically |
| `playwright_sessions` | LinkedIn browser cookies (avoids re-login) | ⚠️ You'll need to re-authenticate |
| `static_files` | Django collected static assets (CSS, JS, images) | ✅ Yes — regenerated by `collectstatic` |

```bash
# List all volumes
docker volume ls | grep CareerBridge

# Inspect a volume
docker volume inspect careerbridge_postgres_data

# Back up PostgreSQL data
docker compose exec db pg_dump -U postgres linkedin_job_alert > backup_$(date +%Y%m%d).sql

# Restore PostgreSQL data
cat backup_20260604.sql | docker compose exec -T db psql -U postgres -d linkedin_job_alert
```

---

### 21.10 Troubleshooting

| Problem | Solution |
|---------|----------|
| `db` service keeps restarting | Check logs: `docker compose logs db`. Usually a password mismatch — delete the volume (`docker compose down -v`) and recreate. |
| `web` can't connect to `db` | Ensure `DB_HOST=db` is set in the `environment` block (not just in `.env`). The container hostname is `db`, not `localhost`. |
| Playwright crashes in worker | Check Docker memory limit. Chromium needs ≥1 GB. On Docker Desktop: Settings → Resources → Memory. |
| Static files not loading | Run `docker compose exec web python manage.py collectstatic --noinput`. |
| Scraper can't log in to LinkedIn | Pre-authenticate on your host machine (see Section 21.8) and ensure the session file is in the `playwright_sessions` volume. |
| Permission denied errors | On Linux, ensure your user is in the `docker` group: `sudo usermod -aG docker $USER`. |
| Port 8000 already in use | Either stop the local Django server or change the host port: `ports: ["8001:8000"]`. |
| Slow build times | Use `docker compose build --parallel` and ensure `.dockerignore` is properly configured. |

---

## 📌 Quick Reference

```bash
# Daily usage — just run this:
python manage.py runserver &
celery -A CareerBridge worker -l info &
celery -A CareerBridge beat -l info &

# Then open: http://localhost:8000
```

```
Scraper runs: Automatically on startup (if not done today) + daily at 08:00
Data stored:  PostgreSQL (jobs.db equivalent but real database)
Dashboard:    http://localhost:8000/jobs/
Analytics:    http://localhost:8000/analytics/
Admin:        http://localhost:8000/admin/
Scraper ctrl: http://localhost:8000/scraper/
```

---

*CareerBridge — Built for people who are serious about their next opportunity.*
*No more frustration. No more missed postings. Just your perfect job, waiting.*
