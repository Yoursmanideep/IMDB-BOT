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
# LOGIN CHECK
# ==========================================
async def login_if_needed(page):
    print("Checking login status...", flush=True)

    # If URL does not contain "login", assume session is active
    if "login" not in page.url.lower():
        print("Already logged in.", flush=True)
        return

    print("Login page detected. Manual login may be required.", flush=True)


# ==========================================
# INSPECT PAGE
# ==========================================
async def inspect_page(page):
    print("Inspecting page...", flush=True)

    await page.wait_for_timeout(15000)

    # Save screenshot for debugging
    await page.screenshot(path="/app/chat_debug.png")
    print("Screenshot saved: /app/chat_debug.png", flush=True)

    # Extract visible page text
    all_text = await page.locator("body").inner_text()

    print("===== PAGE TEXT (FIRST 3000 CHARS) =====", flush=True)
    print(all_text[:3000], flush=True)
    print("===== END PAGE TEXT =====", flush=True)

    # Extract possible clickable items
    buttons = await page.locator('button, a, [role="button"]').all_inner_texts()

    print("===== POSSIBLE CHAT ITEMS =====", flush=True)

    seen = set()
    count = 0

    for item in buttons:
        item = item.strip()

        if len(item) < 2:
            continue

        if item in seen:
            continue

        seen.add(item)

        print(item, flush=True)
        count += 1

        if count >= 20:
            break

    print("===== END CHAT ITEMS =====", flush=True)


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

    print("All environment variables loaded.", flush=True)

    async with async_playwright() as p:
        print("Launching persistent browser...", flush=True)

        # Launch browser with anti-detection settings
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

        # Hide webdriver flag
        await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """)

        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening Snapchat Web...", flush=True)

        # IMPORTANT: use domcontentloaded instead of networkidle
        await page.goto(
            "https://web.snapchat.com",
            wait_until="domcontentloaded",
            timeout=120000
        )

        # Allow extra time for the app to render
        await page.wait_for_timeout(15000)

        print("Title:", await page.title(), flush=True)
        print("URL:", page.url, flush=True)

        await login_if_needed(page)

        # Test AI
        print("AI TEST:", ask_ai("hi"), flush=True)

        # Inspect page contents
        await inspect_page(page)

        # Keep bot running
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
