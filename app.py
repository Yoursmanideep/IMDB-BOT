import os
import asyncio
import traceback
from playwright.async_api import async_playwright

SNAP_USERNAME = os.getenv("SNAP_USERNAME")
SNAP_PASSWORD = os.getenv("SNAP_PASSWORD")


async def main():
    print("=== SNAPCHAT BOT STARTING ===", flush=True)

    print("Username loaded:", bool(SNAP_USERNAME), flush=True)
    print("Password loaded:", bool(SNAP_PASSWORD), flush=True)

    if not SNAP_USERNAME:
        raise ValueError("SNAP_USERNAME is missing.")

    if not SNAP_PASSWORD:
        raise ValueError("SNAP_PASSWORD is missing.")

    async with async_playwright() as p:
        print("Launching Chromium...", flush=True)

        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        print("Browser launched.", flush=True)

        context = await browser.new_context()
        page = await context.new_page()

        print("Opening Snapchat Web...", flush=True)

        await page.goto(
            "https://web.snapchat.com",
            wait_until="domcontentloaded",
            timeout=120000
        )

        print("Snapchat page opened successfully.", flush=True)

        print("Waiting for page to load...", flush=True)
        await page.wait_for_timeout(10000)

        print("Current page title:", await page.title(), flush=True)
        print("Current URL:", page.url, flush=True)

        # Keep alive
        while True:
            print("Bot is still running...", flush=True)
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print("=== ERROR OCCURRED ===", flush=True)
        print(str(e), flush=True)
        traceback.print_exc()
        raise
