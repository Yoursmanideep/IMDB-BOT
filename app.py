import asyncio
from playwright.async_api import async_playwright


async def main():
    print("Starting Snapchat bot...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox"]
        )

        page = await browser.new_page()

        print("Opening Snapchat Web...")
        await page.goto(
            "https://web.snapchat.com",
            wait_until="domcontentloaded"
        )

        print("Snapchat Web opened successfully.")

        # Keep browser alive indefinitely
        while True:
            await asyncio.sleep(60)
            print("Bot is still running..." )


if __name__ == "__main__":
    asyncio.run(main())
