import os
import asyncio
import traceback
import requests
from playwright.async_api import async_playwright

# ==========================================
# ENV VARIABLES
# ==========================================
SNAP_USERNAME = os.getenv("SNAP_USERNAME")
SNAP_PASSWORD = os.getenv("SNAP_PASSWORD")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Persistent browser profile
USER_DATA_DIR = "/app/snap_profile"


# ==========================================
# GROQ TEST FUNCTION
# ==========================================
def ask_ai(text):
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
                    "content": "You are a friendly girl named Rithu. Reply naturally in 1-2 short lines."
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        },
        timeout=30
    )

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# ==========================================
# LOGIN FUNCTION
# ==========================================
async def login_if_needed(page):
    print("Checking login status...", flush=True)

    # Already logged in
    if "login" not in page.url.lower():
        print("Already logged in.", flush=True)
        return

    print("Login required.", flush=True)

    # Try common selectors for username field
    username_selectors = [
        'input[name="username"]',
        'input[type="text"]'
    ]

    username_selector = None

    for selector in username_selectors:
        try:
            await page.wait_for_selector(selector, timeout=5000)
            username_selector = selector
            break
        except:
            pass

    if not username_selector:
        raise Exception("Could not find username field.")

    print("Entering username...", flush=True)
    await page.fill(username_selector, SNAP_USERNAME)

    print("Entering password...", flush=True)
    await page.fill('input[type="password"]', SNAP_PASSWORD)

    print("Submitting login form...", flush=True)
    await page.click('button[type="submit"]')

    print("Waiting for login to complete...", flush=True)
    await page.wait_for_timeout(20000)

    print("Current URL after login:", page.url, flush=True)

    # Save session state
    await page.context.storage_state(path="/app/storage_state.json")
    print("Session saved.", flush=True)


# ==========================================
# MAIN
# ==========================================
async def main():
    print("Starting Snapchat AI Bot...", flush=True)

    if not SNAP_USERNAME:
        raise ValueError("SNAP_USERNAME is missing.")
    if not SNAP_PASSWORD:
        raise ValueError("SNAP_PASSWORD is missing.")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is missing.")

    async with async_playwright() as p:
        print("Launching persistent browser...", flush=True)

        context = await p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=True,
            args=["--no-sandbox"]
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening Snapchat Web...", flush=True)
        await page.goto(
            "https://web.snapchat.com",
            wait_until="networkidle",
            timeout=180000
        )

        print("Title:", await page.title(), flush=True)
        print("URL:", page.url, flush=True)

        # Login if needed
        await login_if_needed(page)

        # Test AI
        print("AI TEST:", ask_ai("hi"), flush=True)

        # Keep running
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
