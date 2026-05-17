import os
import asyncio
import traceback
from playwright.async_api import async_playwright

SNAP_USERNAME = os.getenv("SNAP_USERNAME")
SNAP_PASSWORD = os.getenv("SNAP_PASSWORD")


async def main():
    print("Starting Snapchat bot...", flush=True)

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

        context = await browser.new_context()
        page = await context.new_page()

        print("Opening Snapchat Web...", flush=True)

        await page.goto(
            "https://web.snapchat.com",
            wait_until="networkidle",
            timeout=180000
        )

        print("Page opened.", flush=True)
        print("Title:", await page.title(), flush=True)
        print("URL:", page.url, flush=True)

        # Save screenshot for debugging
        await page.screenshot(path="snapchat_debug.png")
        print("Screenshot saved: snapchat_debug.png", flush=True)

        # Wait a bit more
        await page.wait_for_timeout(10000)

        # Try several possible selectors
        selectors = [
            'input[name="username"]',
            'input[type="text"]',
            'input[placeholder*="Username"]',
            'input[placeholder*="Email"]'
        ]

        found = False

        for selector in selectors:
            try:
                print(f"Trying selector: {selector}", flush=True)
                await page.wait_for_selector(selector, timeout=5000)
                print(f"Found selector: {selector}", flush=True)
                found = True
                break
            except:
                print(f"Not found: {selector}", flush=True)

        if not found:
            print("No login field found.", flush=True)

        # Keep container alive
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
