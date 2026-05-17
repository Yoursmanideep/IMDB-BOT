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

USER_DATA_DIR = "/app/snap_profile"


# ==========================================
# AI FUNCTION
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
                    "content": "You are Rithu, a friendly girl. Reply naturally in 1-2 short lines."
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
# LOGIN CHECK
# ==========================================
async def login_if_needed(page):
    print("Checking login status...", flush=True)

    if "login" not in page.url.lower():
        print("Already logged in.", flush=True)
        return

    raise Exception("Login page detected. Session not saved correctly.")


# ==========================================
# FIND CHATS
# ==========================================
async def inspect_chats(page):
    print("Inspecting chat list...", flush=True)

    # Wait for Snapchat UI to settle
    await page.wait_for_timeout(15000)

    # Save screenshot for debugging
    await page.screenshot(path="/app/chat_debug.png")
    print("Screenshot saved: /app/chat_debug.png", flush=True)

    # Get visible text on page
    all_text = await page.locator("body").inner_text()

    print("===== PAGE TEXT (FIRST 3000 CHARS) =====", flush=True)
    print(all_text[:3000], flush=True)
    print("===== END PAGE TEXT =====", flush=True)

    # Try to collect clickable items that may be chats
    buttons = await page.locator('button, a, [role="button"]').all_inner_texts()

    print("===== POSSIBLE CHAT ITEMS =====", flush=True)

    count = 0
    seen = set()

    for item in buttons:
        item = item.strip()

        if len(item) < 2:
            continue

        if item in seen:
            continue

        seen.add(item)

        print(item, flush=True)
        count += 1

        if count >= 10:
            break

    print("===== END CHAT ITEMS =====", flush=True)


# ==========================================
# MAIN
# ==========================================
async def main():
    print("Starting Snapchat AI Bot...", flush=True)

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

        await login_if_needed(page)

        print("AI TEST:", ask_ai("hi"), flush=True)

        # NEW STEP: inspect chats
        await inspect_chats(page)

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
