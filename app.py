# ==========================================
# PART 1 OF 3 — Imports, Config, ZIP Extraction
# ==========================================

import os
import asyncio
import traceback
import zipfile
import requests
from playwright.async_api import async_playwright

# ==========================================
# ENV VARIABLES
# ==========================================
SNAP_USERNAME = os.getenv("SNAP_USERNAME")
SNAP_PASSWORD = os.getenv("SNAP_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ZIP file uploaded to GitHub
PROFILE_ZIP = "snap_profile.zip"

# Persistent browser profile location used by Playwright
USER_DATA_DIR = "/app/snap_profile"


# ==========================================
# EXTRACT AUTHENTICATED SNAPCHAT SESSION
# ==========================================
def extract_snap_profile():
    try:
        # If already extracted, skip
        if os.path.exists(os.path.join(USER_DATA_DIR, "Default")):
            print("snap_profile already extracted.", flush=True)
            return

        # ZIP file missing
        if not os.path.exists(PROFILE_ZIP):
            print("snap_profile.zip not found.", flush=True)
            return

        print("Extracting snap_profile.zip...", flush=True)

        # Remove empty directory if it exists
        if os.path.exists(USER_DATA_DIR):
            try:
                import shutil
                shutil.rmtree(USER_DATA_DIR)
            except:
                pass

        # Extract ZIP into /app
        # Since ZIP contains the folder "snap_profile",
        # this creates /app/snap_profile/...
        with zipfile.ZipFile(PROFILE_ZIP, "r") as zip_ref:
            zip_ref.extractall("/app")

        print("snap_profile extracted successfully.", flush=True)

    except Exception as e:
        print(
            "Failed to extract snap_profile.zip:",
            str(e),
            flush=True
        )
# ==========================================
# PART 2 OF 3 — AI FUNCTION AND LOGIN
# ==========================================

# ==========================================
# AI FUNCTION (GROQ)
# ==========================================
def ask_ai(text):
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Rithu, a 23-year-old girl. "
                            "You are playful, warm, funny, and natural. "
                            "Reply like a real human texter in 1-2 short lines."
                        )
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "temperature": 0.9
            },
            timeout=30
        )

        data = response.json()

        if "choices" not in data:
            print("GROQ ERROR:", data, flush=True)
            return "Hey 😊"

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("AI ERROR:", e, flush=True)
        return "Oops 😅"


# ==========================================
# LOGIN FUNCTION
# ==========================================
async def login_if_needed(page):
    print("Checking login status...", flush=True)

    body_text = await page.locator("body").inner_text()

    # If login page is still visible, the saved session was not restored
    if "Log in to Snapchat" in body_text:
        print("Login page detected. Saved session was not restored.", flush=True)
        return

    print("Already logged in using saved snap_profile.", flush=True)
# ==========================================
# PART 3 OF 3 — MAIN
# ==========================================

async def main():
    print("Starting Snapchat AI Bot...", flush=True)

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing.")

    print("All environment variables loaded.", flush=True)

    # Extract the authenticated session from snap_profile.zip
    extract_snap_profile()

    async with async_playwright() as p:
        print("Launching persistent browser...", flush=True)

        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=True,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-web-security",
            ]
        )

        # Hide automation flag
        await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """)

        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )

        print("Opening Snapchat Web...", flush=True)

        await page.goto(
            "https://web.snapchat.com",
            wait_until="domcontentloaded",
            timeout=120000
        )

        # Give the app time to load
        await page.wait_for_timeout(15000)

        print("Title:", await page.title(), flush=True)
        print("URL:", page.url, flush=True)

        # Verify that the saved session is working
        await login_if_needed(page)

        # Save screenshot for debugging
        await page.screenshot(path="/app/after_login.png")
        print("Saved screenshot: /app/after_login.png", flush=True)

        # Final state
        print("Final Title:", await page.title(), flush=True)
        print("Final URL:", page.url, flush=True)

        # Test Groq AI
        print("AI TEST:", ask_ai("hi"), flush=True)

        # Keep process alive
        while True:
            print("Bot is still running...", flush=True)
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("ERROR:", str(e), flush=True)
        traceback.print_exc()
        raise
