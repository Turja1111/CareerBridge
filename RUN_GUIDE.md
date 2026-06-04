# 🚀 CareerBridge — Running & Operations Guide

Welcome to the **CareerBridge** execution guide. This document provides step-by-step instructions on how to start and operate your CareerBridge platform smoothly.

---

## ❓ Do Redis and Celery Run Automatically?

- **If running locally (Local Host Way)**: **No**, they do not run automatically. You must start the Redis service and the Celery processes manually in separate terminal windows before running Django.
- **If running via Docker (Recommended)**: **Yes!** When you use Docker Compose, everything (PostgreSQL, Redis, Django Web, Celery Worker, and Celery Beat) starts automatically in the background with a single command.

---

## 🛣️ Path A: The Docker Way (Easiest — Recomended)

Docker runs everything automatically inside isolated containers, meaning you do not need to manually configure Redis or open multiple terminal windows.

### **Step 1: Ensure Docker Desktop is Active**
Open the **Docker Desktop** application on your Windows machine and ensure the Docker engine is running (the status indicator in the bottom-left of Docker Desktop should be green).

### **Step 2: Edit your Credentials**
Open the [`.env`](file:///d:/Projects/CareerBridge/.env) file and add your actual LinkedIn credentials:
```properties
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=yourpassword
```

### **Step 3: Start the Containers**
Open a terminal (e.g. PowerShell or Command Prompt) in the project directory and run:
```bash
docker compose up -d --build
```
This builds the images and spins up Redis, Postgres, Django Web, Celery Worker, and Celery Beat automatically. 

*💡 **Docker Desktop GUI Tip**: You can open the **Docker Desktop** app, go to the **Containers** tab, and you will see the `CareerBridge` container stack. You can view live logs, restart, or stop individual services (like the web server or celery worker) with one click from the interface!*

### **Step 4: Apply Migrations & Create Admin User**
*(Only needed on the first setup)*
```bash
# Run migrations inside the docker container
docker compose exec web python manage.py migrate

# Create a superuser for accessing /admin
docker compose exec web python manage.py createsuperuser
```

### **Step 5: Access the App**
Open your browser and navigate to:
- **Main Dashboard**: `http://localhost:8000/`
- **Job Board**: `http://localhost:8000/jobs/`
- **Scraper Control Panel**: `http://localhost:8000/scraper/`
- **Django Admin Interface**: `http://localhost:8000/admin/`

### **Step 6: Stop the App**
To stop all background services:
* **Via terminal**: Run `docker compose down`
* **Via Docker Desktop**: Click the **Stop** (Square) button next to the `CareerBridge` container stack.

---

## 💻 Path B: The Local Host Way (Manual)

If you prefer to run the application natively on your computer without Docker, you will need to open separate terminal windows.

### **Step 1: Start Redis**
Open a terminal window and run:
- **If using WSL (Linux/Ubuntu on Windows)**:
  ```bash
  sudo service redis-server start
  ```
- **If using Redis for Windows (standalone)**:
  Open `redis-server.exe` or run:
  ```cmd
  redis-server
  ```
*Verify it is running by running `redis-cli ping` (should output `PONG`).*

### **Step 2: Start Celery Worker**
Open a **second** terminal window, navigate to the project root, and run:
```bash
celery -A careerbridge worker -l info --pool=solo
```
*(The `--pool=solo` flag is required on Windows to prevent threading issues).*

### **Step 3: Start Celery Beat Scheduler**
Open a **third** terminal window, navigate to the project root, and run:
```bash
celery -A careerbridge beat -l info
```
*(This triggers the automated daily scraping task).*

### **Step 4: Start Django Web Server**
Open a **fourth** terminal window, navigate to the project root, and run:
```bash
python manage.py runserver
```

---

## 🎯 Operating CareerBridge

### **Pre-authenticating LinkedIn Session (Required once)**
Since LinkedIn implements strict anti-bot measures (like 2FA and CAPTCHAs), it is best to log in manually once so that Playwright can save your cookies.

Run the helper script in your local terminal:
```bash
python login.py
```
This script will check if Playwright is installed on your host system (installing it if missing), launch a Chromium browser window for you to log in, and save your login session to `linkedin_session/session.json`.

Once completed, the scraper running inside Docker will immediately detect and use this session file (via the volume bind-mount) to scrape jobs silently without needing further logins or prompting for 2FA.

### **Running a Scrape Manual Trigger**
1. Access the **Scraper Control Panel** at `http://localhost:8000/scraper/`.
2. Configure your search keywords (e.g. `Python Developer`) and locations (e.g. `Remote`) in the preferences form on the right and click **Save Preferences**.
3. Click the **Trigger Scraper Now** button.
4. The live engine monitor will start polling, showing you how many jobs are being found in real-time.
