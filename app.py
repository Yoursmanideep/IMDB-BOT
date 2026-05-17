import os
import asyncio
from playwright.async_api import async_playwright


SNAP_USERNAME = os.getenv("SNAP_USERNAME")
SNAP_PASSWORD = os.getenv("SNAP_PASSWORD")


async def main():
    print("Starting Snapchat bot...")

    if not SNAP_USERNAME:
        raise ValueError("SNAP_USERNAME is missing.")

    if not SNAP_PASSWORD:
        raise ValueError("SNAP_PASSWORD is missing.")

    async with async_playwright() as p:
        print("Launching Chromium...")

        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        context = await browser.new_context()
        page = await context.new_page()

        print("Opening Snapchat Web...")
        await page.goto(
            "https://web.snapchat.com",
            wait_until="domcontentloaded",
            timeout=120000
        )

        print("Waiting for login fields...")

        # Wait for username and password inputs
        await page.wait_for_selector('input[name="username"]', timeout=60000)
        await page.wait_for_selector('input[name="password"]', timeout=60000)

        print("Entering username...")
        await page.fill('input[name="username"]', SNAP_USERNAME)

        print("Entering password...")
        await page.fill('input[name="password"]', SNAP_PASSWORD)

        print("Clicking Log In...")
        await page.click('button[type="submit"]')

        print("Waiting for Snapchat to load after login...")
        await page.wait_for_timeout(15000)

        print("Login attempt completed.")

        # Keep the bot running so we can inspect logs
        while True:
            await asyncio.sleep(60)
            print("Bot is still running...")


if __name__ == "__main__":
    asyncio.run(main())
