# CareerBridge

CareerBridge is a self-hosted job intelligence dashboard for tracking LinkedIn job opportunities. It uses Django, PostgreSQL, Celery, Redis, and Playwright to scrape matching job posts, deduplicate them, parse useful metadata, and present everything through a personal dashboard with job search, status tracking, and analytics.

> Note: LinkedIn scraping may be subject to LinkedIn's terms of service and anti-automation protections. Use this project responsibly, for personal use, and expect occasional session, CAPTCHA, or selector changes.

## Features

- LinkedIn job scraping with Playwright
- Saved browser session support to reduce repeated logins
- Manual and scheduled scraping through Celery and Celery Beat
- PostgreSQL-backed job, company, skill, and scrape log storage
- Job deduplication by LinkedIn job ID
- Skill, salary, experience level, and work type parsing
- Job board with filters, search, and application status tracking
- Analytics dashboard for skills, companies, locations, work type, salary, and trends
- REST API endpoints for jobs, scraper controls, and analytics
- Docker Compose setup for PostgreSQL, Redis, Django, Celery worker, and Celery Beat

## Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | Django 5 |
| API | Django REST Framework |
| Database | PostgreSQL |
| Task queue | Celery |
| Broker/result backend | Redis |
| Scheduler | Celery Beat / django-celery-beat |
| Scraper | Playwright |
| Frontend | Django templates, static CSS/JS |
| Charts | Chart.js / frontend chart scripts |
| Static files | WhiteNoise |

## Project Structure

```text
CareerBridge/
|-- apps/
|   |-- analytics/        # Dashboard metrics and analytics APIs
|   |-- core/             # Shared base models and utilities
|   |-- dashboard/        # Main dashboard view
|   |-- jobs/             # Job, company, skill, and status models/views
|   `-- scraper/          # Playwright scraper, Celery tasks, logs, preferences
|-- careerbridge/
|   |-- settings/         # base, local, and production settings
|   |-- celery.py         # Celery app and beat schedule
|   `-- urls.py           # Root routes
|-- linkedin_session/     # Saved Playwright session state
|-- static/               # CSS and JavaScript
|-- templates/            # Django templates
|-- docker-compose.yml
|-- Dockerfile
|-- login.py              # Manual LinkedIn session bootstrap helper
|-- manage.py
`-- requirements.txt
```

## Getting Started

### Prerequisites

- Docker Desktop, recommended for the full stack
- Python 3.12, if running locally without Docker
- PostgreSQL and Redis, if running locally without Docker
- A LinkedIn account for manual session creation

## Environment Setup

Copy the example environment file and update the values:

```bash
cp .env.example .env
```

Important variables:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=linkedin_job_alert
DB_USER=postgres
DB_PASSWORD=Admin
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/0

LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword

SCRAPER_MAX_JOBS_PER_SEARCH=30
SCRAPER_DAILY_HOUR=8
SCRAPER_DAILY_MINUTE=0
SCRAPER_HEADLESS=True
SCRAPER_REQUEST_DELAY=2
```

Generate an encryption key for credential storage:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then set:

```env
CREDENTIAL_ENCRYPTION_KEY=generated-key-here
```

If a value in `.env` contains a dollar sign, escape it as `$$` when using Docker Compose.

## Run With Docker

Build and start the full stack:

```bash
docker compose up -d --build
```

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

Open the app:

- Dashboard: http://localhost:8000/
- Jobs: http://localhost:8000/jobs/
- Analytics: http://localhost:8000/analytics/
- Scraper control panel: http://localhost:8000/scraper/
- Admin: http://localhost:8000/admin/

Stop everything:

```bash
docker compose down
```

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

Make sure PostgreSQL and Redis are running, then apply migrations:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the Django server:

```bash
python manage.py runserver
```

In separate terminals, start Celery worker and beat:

```bash
celery -A careerbridge worker -l info --pool=solo
```

```bash
celery -A careerbridge beat -l info
```

The `--pool=solo` flag is recommended on Windows.

## LinkedIn Session Setup

LinkedIn often requires 2FA or CAPTCHA verification. The most reliable flow is to create a saved Playwright session once:

```bash
python login.py
```

A browser window will open. Log in manually, complete any verification, then return to the terminal and press Enter. The script saves cookies and browser state to:

```text
linkedin_session/session.json
```

Docker mounts this folder into the app container, so the scraper can reuse the saved session.

## Scraper Usage

From the scraper control panel:

1. Open http://localhost:8000/scraper/
2. Set keywords and locations.
3. Save preferences.
4. Click the manual trigger button.
5. Watch the current run status and scrape logs.

The scheduled scrape uses the values:

```env
SCRAPER_DAILY_HOUR=8
SCRAPER_DAILY_MINUTE=0
```

The Celery task is:

```text
scraper.run_scrape
```

## API Routes

Scraper:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| POST | `/api/scraper/trigger/` | Start a manual scrape |
| GET | `/api/scraper/status/` | Current scraper status |
| GET | `/api/scraper/logs/` | Recent scrape logs |
| GET/POST | `/api/scraper/preferences/` | Read or update scraper preferences |

Jobs:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/jobs/` | List jobs |
| GET | `/api/jobs/new/` | List recently scraped jobs |
| POST | `/api/jobs/<id>/status/` | Update job status |

Analytics:

| Method | Endpoint |
| --- | --- |
| GET | `/api/analytics/summary/` |
| GET | `/api/analytics/top-skills/` |
| GET | `/api/analytics/jobs-over-time/` |
| GET | `/api/analytics/work-type-distribution/` |
| GET | `/api/analytics/salary-ranges/` |
| GET | `/api/analytics/top-companies/` |
| GET | `/api/analytics/top-locations/` |
| GET | `/api/analytics/skills-by-experience/` |

## Common Commands

Run Django checks:

```bash
python manage.py check
```

Seed demo data, if needed:

```bash
python manage.py seed_demo_data
```

Run a scraper task directly from Django shell:

```bash
python manage.py shell -c "from apps.scraper.tasks import run_scrape_task; print(run_scrape_task(triggered_by='manual'))"
```

View Docker logs:

```bash
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f beat
```

## Troubleshooting

### Scraper says login failed

- Run `python login.py` again and refresh `linkedin_session/session.json`.
- Check that `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` are set.
- Set `SCRAPER_HEADLESS=False` if manual verification is needed.
- Confirm the saved session contains LinkedIn cookies.

### Manual trigger says a scrape is already running

A previous run may still have a `running` log row. Check scraper logs in the UI or in Django admin.

### Docker Compose warns about an unset variable

If a `.env` value contains `$`, Docker Compose may try to interpolate it. Escape dollar signs as `$$`.

### Celery task does not run

- Confirm Redis is running.
- Confirm the Celery worker is running.
- In Docker, check `docker compose ps` and `docker compose logs -f worker`.
- Locally on Windows, start the worker with `--pool=solo`.

### Playwright browser is missing

Install Chromium:

```bash
playwright install chromium
```

In Docker, rebuild the image:

```bash
docker compose build --no-cache
```

## Security Notes

- Never commit `.env`.
- Never commit real LinkedIn credentials.
- Treat `linkedin_session/session.json` as sensitive because it contains authenticated cookies.
- Rotate credentials if a session file or environment file is exposed.
- Use a strong `SECRET_KEY` and `CREDENTIAL_ENCRYPTION_KEY`.

## Development Notes

- Keep scraper selector changes isolated in `apps/scraper/playwright_engine.py`.
- Keep parsing logic in `apps/scraper/parser.py`.
- Job persistence and deduplication happen through `apps/jobs/models.py`.
- Background execution starts in `apps/scraper/tasks.py`.
- The daily schedule is configured in `careerbridge/celery.py`.

## License

This project is currently unlicensed. Add a license file before distributing or accepting external contributions.
