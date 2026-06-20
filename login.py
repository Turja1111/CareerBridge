import os
import asyncio
import sys

def main():
    # Ensure playwright is installed, or try importing it
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Playwright is not installed. Installing now...")
        os.system(f"{sys.executable} -m pip install playwright")
        os.system(f"{sys.executable} -m playwright install chromium")
        from playwright.async_api import async_playwright

    async def run_login():
        print("Launching Chromium browser in headed mode...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
            page = await context.new_page()
            
            print("Navigating to LinkedIn login page...")
            await page.goto('https://www.linkedin.com/login')
            
            print("\n*** Action Required ***")
            print("Please log in manually in the opened browser window.")
            print("Solve any CAPTCHAs or 2FA checks.")
            print("After you see your LinkedIn feed, press Enter here to save your session...")
            
            # Wait for user input
            input("Press Enter after logging in...")
            
            # Verify user is actually logged in before saving
            print("Verifying login status...")
            await page.goto('https://www.linkedin.com/feed/')
            await page.wait_for_timeout(3000)
            
            # Check if we're on the feed page (logged in) or still on login page
            current_url = page.url
            if '/login' in current_url or 'login' in current_url:
                print("\n⚠️  WARNING: You are still on the login page!")
                print("The session will NOT be saved until you complete login.")
                print("Please log in first, then press Enter again.")
                input("Press Enter after you see your LinkedIn feed...")
                await page.goto('https://www.linkedin.com/feed/')
                await page.wait_for_timeout(3000)
                current_url = page.url
            
            # Ensure the directory exists
            os.makedirs("linkedin_session", exist_ok=True)
            await context.storage_state(path='linkedin_session/session.json')
            await browser.close()
            
            if '/feed' in current_url or '/jobs' in current_url:
                print("\n✅ Session saved successfully to linkedin_session/session.json!")
            else:
                print("\n⚠️  Session saved, but login status is uncertain. Current URL:", current_url)

    try:
        asyncio.run(run_login())
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure your Python environment is working and has internet access.")

if __name__ == "__main__":
    main()
