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
            input("Once you see your LinkedIn feed, return here and press Enter to save your session...")
            
            # Ensure the directory exists
            os.makedirs("linkedin_session", exist_ok=True)
            await context.storage_state(path='linkedin_session/session.json')
            await browser.close()
            print("\nSession saved successfully to linkedin_session/session.json!")

    try:
        asyncio.run(run_login())
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure your Python environment is working and has internet access.")

if __name__ == "__main__":
    main()
