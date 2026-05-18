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
# Replace ONLY the login_if_needed() function in your app.py
# This version performs the login step-by-step:
# 1. Detect login page
# 2. Enter username
# 3. Press Enter
# 4. Wait for password field
# 5. Enter password
# 6. Press Enter
# 7. Wait for "Is This You?" verification
# 8. Wait until login completes

# Replace ONLY the login_if_needed() function in app.py
# This version uses a robust approach:
# 1. Finds ALL input fields
# 2. Ignores Search and hidden fields
# 3. Types username
# 4. Waits for password field
# 5. Types password
# 6. Waits for verification and successful login

# Replace ONLY the login_if_needed(page) function with this final version.
# Snapchat is redirecting directly to a verification/captcha URL
# immediately after the username is submitted. That means the password
# field may never appear. This function handles BOTH cases:
# 1. Password field appears -> enter password
# 2. Verification page appears directly -> wait for phone approval

async def login_if_needed(page):
    print("Checking login status...", flush=True)

    await page.wait_for_timeout(10000)

    body_text = await page.locator("body").inner_text()

    # Already logged in
    if "Log in to Snapchat" not in body_text:
        print("Already logged in.", flush=True)
        return

    print("Login page detected.", flush=True)

    try:
        # ==========================================
        # STEP 1: FIND USERNAME FIELD
        # ==========================================
        print("Locating all input fields...", flush=True)

        inputs = page.locator("input")
        count = await inputs.count()

        print(f"Found {count} input fields.", flush=True)

        username_field = None

        for i in range(count):
            try:
                field = inputs.nth(i)

                if not await field.is_visible():
                    continue

                input_type = await field.get_attribute("type")
                placeholder = await field.get_attribute("placeholder")
                value = await field.input_value()

                print(
                    f"Input {i}: "
                    f"type={input_type}, "
                    f"placeholder={placeholder}, "
                    f"value={value}",
                    flush=True
                )

                # Ignore search box
                if placeholder == "Search":
                    continue

                # Ignore password field
                if input_type == "password":
                    continue

                # Ignore prefilled fields
                if value and value.strip():
                    continue

                username_field = field
                print(f"Using input {i} as username field.", flush=True)
                break

            except Exception:
                pass

        if username_field is None:
            raise Exception("No usable username field found.")

        # ==========================================
        # STEP 2: ENTER USERNAME
        # ==========================================
        print("Entering username...", flush=True)
        await username_field.click()
        await username_field.fill("")
        await username_field.type(SNAP_USERNAME, delay=100)

        # ==========================================
        # STEP 3: SUBMIT USERNAME
        # ==========================================
        print("Submitting username...", flush=True)
        await username_field.press("Enter")

        # Give Snapchat time to navigate
        await page.wait_for_timeout(8000)

        print("Current URL after username:", page.url, flush=True)

        # ==========================================
        # STEP 4: CHECK IF SNAPCHAT SKIPPED PASSWORD
        # ==========================================
        if "captcha" in page.url or "verify" in page.url:
            print(
                "Verification page detected immediately after username.",
                flush=True
            )
        else:
            # Try to find password field
            password_field = page.locator('input[type="password"]').first

            if await password_field.count() > 0:
                print("Password field detected.", flush=True)

                print("Entering password...", flush=True)
                await password_field.click()
                await password_field.fill("")
                await password_field.type(SNAP_PASSWORD, delay=100)

                print("Submitting password...", flush=True)
                await password_field.press("Enter")

                try:
                    await page.locator(
                        'button:has-text("Log in")'
                    ).first.click(timeout=3000)
                    print("Clicked Log In button.", flush=True)
                except:
                    pass

                print("Password submitted.", flush=True)
            else:
                print(
                    "Password field did not appear. "
                    "Continuing to verification wait.",
                    flush=True
                )

    except Exception as e:
        print("Login automation error:", str(e), flush=True)
        return

    # ==========================================
    # STEP 5: WAIT FOR PHONE VERIFICATION
    # ==========================================
    print("Waiting for verification on your phone...", flush=True)
    print("Approve the Snapchat notification if prompted.", flush=True)

    for i in range(60):  # 5 minutes
        await page.wait_for_timeout(5000)

        try:
            current_text = await page.locator("body").inner_text()
        except:
            current_text = ""

        # Detect Snapchat verification states
        if "Is This You?" in current_text:
            print("Is This You? screen detected.", flush=True)

        if "Verifying Your Request" in current_text:
            print(
                "Verification request sent. Check your phone now.",
                flush=True
            )

        if "unable to process your request" in current_text.lower():
            print(
                "Snapchat could not complete verification.",
                flush=True
            )

        # Successful login conditions
        if (
            "Log in to Snapchat" not in current_text
            and "Verifying Your Request" not in current_text
            and "Is This You?" not in current_text
            and "unable to process your request"
            not in current_text.lower()
        ):
            print("Login successful!", flush=True)
            print("Current URL:", page.url, flush=True)
            return

        # Progress update every 30 seconds
        if (i + 1) % 6 == 0:
            elapsed = (i + 1) * 5
            print(f"Still waiting... {elapsed} seconds", flush=True)

    print("Login did not complete within 5 minutes.", flush=True)

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
