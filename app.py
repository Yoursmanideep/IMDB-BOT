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

# Persistent session folder
USER_DATA_DIR = "/app/snap_profile"

# Simple memory per user
user_memory = {}


# ==========================================
# AI FUNCTION (GROQ)
# ==========================================
def ask_ai(user_id, text):
    try:
        if not GROQ_API_KEY:
            return "My brain is offline right now 😅"

        if user_id not in user_memory:
            user_memory[user_id] = []

        # Save user message
        user_memory[user_id].append({
            "role": "user",
            "content": text
        })

        # Keep last 6 messages
        user_memory[user_id] = user_memory[user_id][-6:]

        system_prompt = {
            "role": "system",
            "content": """
You are Rithu Sharma, a 23-year-old girl.

Personality:
- Funny and playful
- Friendly and warm
- Natural human texting style
- Sometimes teasing
- Not robotic

Rules:
- Keep replies short (1-2 lines)
- Sometimes ask questions back
- Never sound like an AI assistant
"""
        }

        messages = [system_prompt] + user_memory[user_id]

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": messages,
                "temperature": 0.9
            },
            timeout=30
        )

        data = response.json()

        if "choices" not in data:
            print("GROQ ERROR:", data)
            return "Hmm, I got distracted 😅"

        reply = data["choices"][0]["message"]["content"].strip()

        # Save assistant reply
        user_memory[user_id].append({
            "role": "assistant",
            "content": reply
        })

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "Oops, my brain lagged for a second 😭"


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
            args=["--no-sandbox"]
        )

        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening Snapchat Web...", flush=True)

        await page.goto(
            "https://web.snapchat.com",
            wait_until="networkidle",
            timeout=180000
        )

        print("Snapchat opened successfully.", flush=True)
        print("Title:", await page.title(), flush=True)
        print("URL:", page.url, flush=True)

        # Test AI
        test_reply = ask_ai("test_user", "hi")
        print("AI TEST REPLY:", test_reply, flush=True)

        # Keep alive
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
