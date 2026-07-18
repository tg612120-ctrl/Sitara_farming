import os
import random
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# ==========================================
# CONFIG
# ==========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

SESSION_STRINGS = [
    s.strip()
    for s in os.getenv("SESSION_STRINGS", "").split(",")
    if s.strip()
]

TARGET_BOT = "patrickstarsrobot"

# ==========================================
# GLOBAL STORAGE
# ==========================================

conversation_locks = {}

# ==========================================
# HELPERS
# ==========================================

async def random_delay():
    await asyncio.sleep(random.uniform(0.2, 0.8))

async def wait_for_buttons(conv, max_messages=10):
    for _ in range(max_messages):
        try:
            msg = await conv.get_response(timeout=10)
            if msg and msg.buttons:
                return msg
        except asyncio.TimeoutError:
            break
    return None

async def click_button(message, keyword):
    if not message.buttons:
        return False
    keyword = keyword.lower()
    for row in message.buttons:
        for button in row:
            if keyword in button.text.lower():
                await random_delay()
                await button.click()
                return True
    return False

def solve_math(text):
    # Matches "43 + 48 = ?" or similar
    import re
    match = re.search(r"(\d+)\s*([\+\-\*\/])\s*(\d+)", text)
    if not match:
        return None
    a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op == '/' and b != 0: return a // b
    return None

# ==========================================
# TASKS
# ==========================================

async def perform_clicker_task(client, account_num):
    lock = conversation_locks[account_num]
    async with lock:
        try:
            async with client.conversation(TARGET_BOT, timeout=60) as conv:
                await conv.send_message("/start")
                menu = await wait_for_buttons(conv)
                if not menu or not await click_button(menu, "Кликер"):
                    return
                
                try:
                    # Wait for math equation or reward response
                    response = await conv.get_response(timeout=15)
                    if response and ("=" in response.raw_text):
                        ans = solve_math(response.raw_text)
                        if ans is not None:
                            await click_button(response, str(ans))
                except asyncio.TimeoutError:
                    pass
        except Exception as e:
            print(f"❌ [{account_num}] Clicker Error: {e}")

# ==========================================
# ACCOUNT
# ==========================================

async def run_account(session_string, account_num):
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ [{account_num}] {me.first_name} connected")
        conversation_locks[account_num] = asyncio.Lock()
        
        # Start clicker loop for this account
        asyncio.create_task(clicker_loop(client, account_num))
    except Exception as e:
        print(f"❌ [{account_num}] Startup Error: {e}")

async def clicker_loop(client, account_num):
    while True:
        await perform_clicker_task(client, account_num)
        # Wait 10 minutes (600 seconds) before next run
        await asyncio.sleep(600)

# ==========================================
# MAIN
# ==========================================

async def main():
    if not SESSION_STRINGS: return
    tasks = [asyncio.create_task(run_account(s, i+1)) for i, s in enumerate(SESSION_STRINGS)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

