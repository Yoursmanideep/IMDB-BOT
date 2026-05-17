# ==========================================
# PART 1 OF 2 — Imports, Config, AI Function
# ==========================================

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
# LOGIN FUNCTION
# ==========================================
async def login_if_needed(page):
    print("Checking login status...", flush=True)

    body_text = await page.locator("body").inner_text()

    if "Log in to Snapchat" in body_text:
        print("Login page detected.", flush=True)

        try:
            print("Locating all input fields...", flush=True)

            # Get all input elements currently visible
            inputs = page.locator("input")
            count = await inputs.count()

            print(f"Found {count} input fields.", flush=True)

            username_filled = False

            # Try every input until one accepts the username
            for i in range(count):
                try:
                    field = inputs.nth(i)
                    input_type = await field.get_attribute("type")
                    placeholder = await field.get_attribute("placeholder")

                    print(
                        f"Input {i}: type={input_type}, placeholder={placeholder}",
                        flush=True
                    )

                    # Skip password fields
                    if input_type == "password":
                        continue

                    # Try filling username
                    await field.fill(SNAP_USERNAME)
                    username_filled = True
                    print(f"Username entered into input {i}.", flush=True)
                    break

                except Exception:
                    pass

            if not username_filled:
                print("Could not find a usable username field.", flush=True)
            else:
                # Fill password
                print("Locating password field...", flush=True)
                await page.fill('input[type="password"]', SNAP_PASSWORD)
                print("Password entered.", flush=True)

                # Click Log In button
                print("Clicking Log In button...", flush=True)
                await page.locator('button:has-text("Log in")').first.click()
                print("Login submitted.", flush=True)

        except Exception as e:
            print("Login automation error:", str(e), flush=True)

        print("Waiting up to 5 minutes for Snapchat verification...", flush=True)
        print("Approve the login request on your phone if Snapchat asks.", flush=True)

        # Wait up to 5 minutes
        for i in range(60):
            await page.wait_for_timeout(5000)

            try:
                current_text = await page.locator("body").inner_text()
            except:
                current_text = ""

            # Login succeeds when login page disappears
            if "Log in to Snapchat" not in current_text:
                print("Login successful!", flush=True)
                print("Current URL:", page.url, flush=True)
                return

            if (i + 1) % 6 == 0:
                print(
                    f"Still waiting... {(i + 1) * 5} seconds",
                    flush=True
                )

        print("Login not completed within 5 minutes.", flush=True)
        return

    print("Already logged in.", flush=True)


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

        # Hide navigator.webdriver
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

        # Allow page to render
        await page.wait_for_timeout(15000)

        print("Title:", await page.title(), flush=True)
        print("URL:", page.url, flush=True)

        # Login and wait for verification approval
        await login_if_needed(page)

        # Save screenshot after login attempt
        await page.screenshot(path="/app/after_login.png")
        print("Saved screenshot: /app/after_login.png", flush=True)

        # Final state
        print("Final Title:", await page.title(), flush=True)
        print("Final URL:", page.url, flush=True)

        # Test Groq AI
        print("AI TEST:", ask_ai("hi"), flush=True)

        # Keep running indefinitely
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
