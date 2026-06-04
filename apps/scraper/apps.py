from django.apps import AppConfig


class ScraperConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.scraper"
    verbose_name = "Scraper"

    def ready(self):
        """On Django startup, check if we need to run a scrape today."""
        import os

        # Only run in the main process, not in migrations or shell
        if os.environ.get("RUN_MAIN") == "true":
            try:
                from .scheduler import startup_scrape_check
                startup_scrape_check()
            except Exception:
                pass  # Don't block server startup
