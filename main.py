import os
import re
import random
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntitySpoiler

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRINGS = [s.strip() for s in os.getenv("SESSION_STRINGS", "").split(",") if s.strip()]
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_BOT = "patrickstarsrobot"

# --- STORAGE ---
conversation_locks = {}
last_redeemed = {}
last_message_ids = {}
processing_promos = set() # Global tracking for single promo

# --- HELPERS ---
async def random_delay():
    await asyncio.sleep(random.uniform(0.2, 0.5))

async def wait_for_buttons(conv, max_messages=10):
    for _ in range(max_messages):
        try:
            msg = await conv.get_response(timeout=10)
            if msg and msg.buttons: return msg
        except: break
    return None

async def click_button(message, keyword):
    if not message or not message.buttons: return False
    for row in message.buttons:
        for button in row:
            if keyword.lower() in button.text.lower():
                await button.click()
                return True
    return False

def extract_promocode(message):
    if message.entities:
        for entity in message.entities:
            if isinstance(entity, MessageEntitySpoiler):
                return message.raw_text[entity.offset:entity.offset+entity.length]
    return None

# --- YOUR EXISTING LOGIC (TOUCHED NOT) ---
def solve_math(text):
    match = re.search(r"(\d+)\s*([+-*/])\s*(\d+)", text)
    if not match: return None
    a, op, b = int(match.group(1)), match.group(2), int(match.group(3))
    if op == '+': return a + b
    if op == '-': return a - b
    if op == '*': return a * b
    if op == '/' and b != 0: return a // b
    return None

async def perform_clicker_task(client, account_num):
    lock = conversation_locks[account_num]
    if lock.locked(): return # Priority check: promo chal raha ho to clicker ruk jaega
    async with lock:
        try:
            async with client.conversation(TARGET_BOT, timeout=30) as conv:
                await conv.send_message("/start")
                menu = await wait_for_buttons(conv)
                if not menu or not await click_button(menu, "Кликер"): return
                try:  
                    response = await conv.get_response(timeout=15)  
                    if response and ("=" in response.raw_text):  
                        ans = solve_math(response.raw_text)  
                        if ans is not None: await click_button(response, str(ans))  
                except: pass  
        except: pass

# --- PROMOCODE PRIORITY LOGIC ---
async def process_promo_for_client(client, account_num, promo_code):
    lock = conversation_locks[account_num]
    async with lock: # Lock ensure karta hai ki clicker nahi chalega
        try:
            async with client.conversation(TARGET_BOT, timeout=60) as conv:
                await conv.send_message("/start")
                m1 = await wait_for_buttons(conv)
                if not await click_button(m1, "Профиль"): return
                
                m2 = await wait_for_buttons(conv)
                if not await click_button(m2, "Промокод"): return
                
                await conv.send_message(promo_code)
                print(f"✅ [{account_num}] Promo Clammed!")
        except Exception as e:
            print(f"❌ [{account_num}] Error: {e}")

async def run_promocode_batch(clients_list, promo_code):
    # Batch 5-5 ka logic
    for i in range(0, len(clients_list), 5):
        batch = clients_list[i:i+5]
        tasks = [process_promo_for_client(c, idx, promo_code) for c, idx in batch]
        await asyncio.gather(*tasks)
        if i + 5 < len(clients_list):
            await asyncio.sleep(3) # 3 sec ka gap

# --- ACCOUNT RUNNER ---
async def run_account(session_string, account_num, client_ref):
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    await client.start()
    conversation_locks[account_num] = asyncio.Lock()
    last_message_ids[account_num] = 0
    client_ref[account_num] = client
    
    # Clicker loop
    asyncio.create_task(clicker_loop(client, account_num))
    return client

async def clicker_loop(client, account_num):
    while True:
        await perform_clicker_task(client, account_num)
        await asyncio.sleep(600)

async def main():
    clients_map = {}
    clients_data = []
    
    # Init sessions
    for i, s in enumerate(SESSION_STRINGS):
        c = await run_account(s, i+1, clients_map)
        clients_data.append((c, i+1))
    
    channel = await clients_map[1].get_entity(SOURCE_CHANNEL)
    
    print("🚀 Bot Started...")
    while True:
        try:
            msg = await clients_map[1].get_messages(channel, limit=1)
            if msg:
                promo = extract_promocode(msg[0])
                if promo and promo not in processing_promos:
                    processing_promos.add(promo)
                    print(f"🔥 Found Promo: {promo}")
                    await run_promocode_batch(clients_data, promo)
                    processing_promos.discard(promo)
            await asyncio.sleep(2)
        except: await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

