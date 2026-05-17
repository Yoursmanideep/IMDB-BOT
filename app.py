# ==========================================
# PART 1 OF 2 — Snapchat AI Bot
# Imports, Configuration, AI, and Login
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

            inputs = page.locator("input")
            count = await inputs.count()

            print(f"Found {count} input fields.", flush=True)

            username_field = None

            # Find visible non-search text field
            for i in range(count):
                try:
                    field = inputs.nth(i)
                    input_type = await field.get_attribute("type")
                    placeholder = await field.get_attribute("placeholder")

                    print(
                        f"Input {i}: type={input_type}, "
                        f"placeholder={placeholder}",
                        flush=True
                    )

                    # Ignore search box
                    if placeholder == "Search":
                        continue

                    # Ignore password fields
                    if input_type == "password":
                        continue

                    username_field = field
                    print(
                        f"Using input {i} as username field.",
                        flush=True
                    )
                    break

                except Exception:
                    pass

            if username_field is None:
                print("No suitable username field found.", flush=True)
            else:
                print("Entering username...", flush=True)
                await username_field.click()
                await username_field.fill(SNAP_USERNAME)

                print("Submitting username step...", flush=True)
                await username_field.press("Enter")

                # Wait for password field to appear
                await page.wait_for_timeout(5000)

                password_locator = page.locator(
                    'input[type="password"]'
                )

                if await password_locator.count() > 0:
                    print("Password field detected.", flush=True)

                    await password_locator.first.fill(
                        SNAP_PASSWORD
                    )

                    print("Password entered.", flush=True)

# ==========================================
# PART 2 OF 2 — Finish Login and Main
# ==========================================

                    print("Submitting password step...", flush=True)
                    await password_locator.first.press("Enter")

                    # Optional extra click if Log In button is visible
                    try:
                        await page.locator(
                            'button:has-text("Log in")'
                        ).first.click(timeout=3000)
                        print("Clicked Log In button.", flush=True)
                    except:
                        pass

                    print("Login submitted.", flush=True)
                else:
                    print(
                        "Password field did not appear yet.",
                        flush=True
                    )

        except Exception as e:
            print("Login automation error:", str(e), flush=True)

        print(
            "Waiting up to 5 minutes for Snapchat verification...",
            flush=True
        )
        print(
            "Approve the request in your Snapchat mobile app.",
            flush=True
        )

        # Wait up to 5 minutes (60 × 5 seconds)
        for i in range(60):
            await page.wait_for_timeout(5000)

            try:
                current_text = await page.locator(
                    "body"
                ).inner_text()
            except:
                current_text = ""

            # Detect verification screen
            if "Is This You?" in current_text:
                print(
                    "Verification prompt detected! "
                    "Check your phone now.",
                    flush=True
                )

            # Successful login when login text disappears
            if "Log in to Snapchat" not in current_text:
                print("Login successful!", flush=True)
                print("Current URL:", page.url, flush=True)
                return

            # Progress update every 30 seconds
            if (i + 1) % 6 == 0:
                elapsed = (i + 1) * 5
                print(
                    f"Still waiting... {elapsed} seconds",
                    flush=True
                )

        print(
            "Login not completed within 5 minutes.",
            flush=True
        )
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

        await page.wait_for_timeout(15000)

        print("Title:", await page.title(), flush=True)
        print("URL:", page.url, flush=True)

        # Perform login and wait for phone verification
        await login_if_needed(page)

        # Save screenshot after login attempt
        await page.screenshot(path="/app/after_login.png")
        print("Saved screenshot: /app/after_login.png", flush=True)

        # Final page state
        print("Final Title:", await page.title(), flush=True)
        print("Final URL:", page.url, flush=True)

        # Test AI connection
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
