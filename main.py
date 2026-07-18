import os
import re
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

SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_BOT = "patrickstarsrobot"

# ==========================================
# GLOBAL STORAGE
# ==========================================

conversation_locks = {}
last_redeemed = {}
last_message_ids = {}
processing_promos = {}

# ==========================================
# HELPERS
# ==========================================

async def random_delay():
    await asyncio.sleep(random.uniform(0.2, 0.8))

async def wait_for_buttons(conv, max_messages=10):
    for _ in range(max_messages):
        try:
            msg = await conv.get_response(timeout=10)
            if msg.buttons:
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

def extract_promocode(text):
    match = re.search(r"[A-Za-z0-9_]{6,}$", text)
    return match.group(0) if match else None

def solve_math(text):
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
            async with client.conversation(TARGET_BOT, timeout=30) as conv:
                await conv.send_message("/start")
                menu = await wait_for_buttons(conv)
                if not menu or not await click_button(menu, "Кликер"):
                    return
                
                try:
                    response = await conv.get_response(timeout=15)
                    if response and ("=" in response.raw_text):
                        ans = solve_math(response.raw_text)
                        if ans is not None:
                            await click_button(response, str(ans))
                except asyncio.TimeoutError:
                    pass
        except Exception as e:
            print(f"❌ [{account_num}] Clicker Error: {e}")

async def perform_interaction(client, account_num, promo_code):
    if last_redeemed.get(account_num) == promo_code:
        processing_promos[account_num].discard(promo_code)
        return
    lock = conversation_locks[account_num]
    async with lock:
        try:
            await random_delay()
            async with client.conversation(TARGET_BOT, timeout=60) as conv:
                await conv.send_message("/start")
                main_menu = await wait_for_buttons(conv)
                if not main_menu or not await click_button(main_menu, "Профиль"):
                    return
                second_menu = await wait_for_buttons(conv)
                if not second_menu or not await click_button(second_menu, "Промокод"):
                    return
                try: await conv.get_response(timeout=10)
                except: pass
                await random_delay()
                await conv.send_message(promo_code)
                last_redeemed[account_num] = promo_code
        except Exception as e:
            print(f"❌ [{account_num}] Redeem Error: {e}")
        finally:
            processing_promos[account_num].discard(promo_code)

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
        last_redeemed[account_num] = None
        last_message_ids[account_num] = 0
        processing_promos[account_num] = set()
        channel = await client.get_entity(SOURCE_CHANNEL)
        asyncio.create_task(clicker_loop(client, account_num))
    except Exception as e:
        print(f"❌ [{account_num}] Startup Error: {e}")
        return

    while True:
        try:
            messages = await client.get_messages(channel, limit=1)
            if messages:
                message = messages[0]
                if message.id > last_message_ids[account_num]:
                    last_message_ids[account_num] = message.id
                    promo = extract_promocode(message.raw_text or "")
                    if promo and promo not in processing_promos[account_num]:
                        processing_promos[account_num].add(promo)
                        asyncio.create_task(perform_interaction(client, account_num, promo))
            await asyncio.sleep(2)
        except Exception as e:
            print(f"❌ [{account_num}] Polling Error: {e}")
            await asyncio.sleep(5)

async def clicker_loop(client, account_num):
    # Pehli baar turant run hoga, fir har 10 min
    while True:
        await perform_clicker_task(client, account_num)
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

