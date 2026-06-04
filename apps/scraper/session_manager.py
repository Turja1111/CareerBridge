"""
Scraper — Session manager for Playwright browser cookies.

Handles saving and loading LinkedIn session state
so the scraper doesn't need to log in every time.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SESSION_DIR = Path(__file__).resolve().parent.parent.parent / "linkedin_session"
SESSION_FILE = SESSION_DIR / "session.json"


def ensure_session_dir():
    """Create the session directory if it doesn't exist."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)


async def save_session(context):
    """
    Save browser context storage state (cookies + localStorage).
    This avoids re-login for weeks.
    """
    try:
        ensure_session_dir()
        storage_state = await context.storage_state()
        with open(SESSION_FILE, "w") as f:
            json.dump(storage_state, f, indent=2)
        logger.info(f"Session saved to {SESSION_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to save session: {e}")
        return False


async def load_session(browser):
    """
    Create a new browser context with saved session state.
    Returns None if no saved session exists.
    """
    if not SESSION_FILE.exists():
        logger.info("No saved session found. Will need to login.")
        return None

    try:
        context = await browser.new_context(
            storage_state=str(SESSION_FILE),
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        logger.info("Loaded saved session from disk.")
        return context
    except Exception as e:
        logger.warning(f"Failed to load session (may be expired): {e}")
        return None


def has_saved_session():
    """Check if a saved session file exists."""
    return SESSION_FILE.exists()


def delete_session():
    """Delete the saved session file (for logout or session refresh)."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
        logger.info("Saved session deleted.")
