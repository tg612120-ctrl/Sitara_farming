import os
import re
import random
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==========================================
# CONFIG
# ==========================================
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")

SESSION_STRINGS = [
    s.strip()
    for s in os.getenv("SESSION_STRINGS", "").split(",")
    if s.strip()
]

SOURCE_CHANNEL = "patrickstarsfarm" 
TARGET_BOT = "patrickstarsrobot"

# ==========================================
# GLOBAL STORAGE
# ==========================================
conversation_locks = {}
last_redeemed = {}
processing_promos = {}

# ==========================================
# HELPERS
# ==========================================
async def random_delay(min_s=0.5, max_s=1.5):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def wait_for_buttons(account_num, conv, task_name, timeout=12):
    """
    [FIXED]: Agar bot intro text ya photo bhejta hai (bina button ke), 
    to ye automatic agle message ka wait karega jab tak buttons na mil jayein.
    """
    try:
        for _ in range(4): # Max 4 messages tak check karega continuous stream mein
            msg = await conv.get_response(timeout=timeout)
            if msg:
                if msg.buttons:
                    return msg
                else:
                    # Agar text/photo hai bina button ke, to skip karke aage badho
                    await asyncio.sleep(0.3)
    except asyncio.TimeoutError:
        print(f"⏰ [{account_num}][{task_name}] Log: Timeout waiting for buttons.")
    except Exception as e:
        print(f"❌ [{account_num}][{task_name}] Log: Error waiting for buttons: {e}")
    return None

async def click_button(account_num, message, keyword, task_name):
    if not message or not message.buttons:
        return False
        
    keyword = keyword.lower()
    for row in message.buttons:
        for button in row:
            if keyword in button.text.lower():
                await random_delay()
                try:
                    await button.click()
                    print(f"🎯 [{account_num}][{task_name}] Log: Clicked button '{button.text}'")
                    return True
                except Exception as e:
                    print(f"❌ [{account_num}][{task_name}] Log: Failed clicking '{button.text}': {e}")
                    return False
    return False

def extract_promocode(message_obj):
    """
    [SPOILER & CODE DETECTOR]: Yeh check karta hai ki kya text mein koi spoiler word hai 
    ya standard format hai, aur usme se alphanumeric promo code extract karta hai.
    """
    if not message_obj or not message_obj.raw_text:
        return None
        
    text = message_obj.raw_text
    
    # Telegram markdown ya entities mein MessageEntitySpoiler check karne ke liye
    has_spoiler = False
    if message_obj.entities:
        for entity in message_obj.entities:
            if type(entity).__name__ == 'MessageEntitySpoiler':
                has_spoiler = True
                break
                
    # Agar explicit format ya '||' (spoiler marker) text mein ho
    if "||" in text:
        has_spoiler = True

    # Promo code alag nikalne ke liye regex (6 ya usse bade capital/alphanumeric words)
    matches = re.findall(r"\b[A-Za-z0-9_]{6,}\b", text)
    for match in matches:
        # Ignore common layout/menu words
        if match.lower() not in ["кликер", "профиль", "промокод", "start", "help", "stars"]:
            # Agar spoiler detected hai ya code standard format mein hai, use validate karein
            return match
            
    return None

def solve_math(text):
    # Matches patterns like "5 + 3", "12 - 4", etc.
    match = re.search(r"(\d+)\s*([+\-*/])\s*(\d+)", text)
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
    """
    [TASK 1]: Har 10 min mein '/start' -> Click 'Кликер'. 
    Agar math captcha aaya to solve karega, nahi aaya to click karke chhod dega.
    """
    lock = conversation_locks.get(account_num)
    if not lock: return
    
    async with lock:
        try:
            print(f"🔄 [{account_num}][Clicker] Log: Executing 10-minute automated click...")
            async with client.conversation(TARGET_BOT, timeout=30) as conv:
                await conv.send_message("/start")
                
                # Main menu aane ka wait karein aur 'Кликер' click karein
                menu = await wait_for_buttons(account_num, conv, "Clicker")
                if not menu or not await click_button(account_num, menu, "Кликер", "Clicker"):
                    return

                # Clicker interface/response ka wait karein
                response = await wait_for_buttons(account_num, conv, "Clicker")
                if response and response.raw_text:
                    # Agar mathematics (addition/subtraction) captcha dikhta hai
                    if "=" in response.raw_text or any(op in response.raw_text for op in ["+", "-", "*"]):
                        ans = solve_math(response.raw_text)
                        if ans is not None:
                            print(f"🔢 [{account_num}][Clicker] Log: Math Captcha Found: {response.raw_text.strip()} -> Solving: {ans}")
                            await click_button(account_num, response, str(ans), "Clicker")
                        else:
                            print(f"ℹ️ [{account_num}][Clicker] Log: Clicked 'Кликер' successfully. No valid math equation parsed.")
                    else:
                        print(f"ℹ️ [{account_num}][Clicker] Log: Clicked 'Кликер' successfully. Normal interface (No math captcha).")
        except Exception as e:
            print(f"❌ [{account_num}][Clicker] Execution Error: {e}")

async def perform_interaction(client, account_num, promo_code):
    """
    [TASK 2]: Source channel mein new post aane par: 
    '/start' -> Click 'Профиль' -> Response Wait -> Click 'Промокод' -> Send Code.
    """
    if last_redeemed.get(account_num) == promo_code:
        return
        
    lock = conversation_locks.get(account_num)
    if not lock: return
    
    async with lock:
        try:
            print(f"🚀 [{account_num}][Redeem] Log: Processing promo code [{promo_code}]...")
            async with client.conversation(TARGET_BOT, timeout=40) as conv:
                await conv.send_message("/start")
                
                # 1. Main menu se 'Профиль' par click karein
                main_menu = await wait_for_buttons(account_num, conv, "Redeem")
                if not main_menu or not await click_button(account_num, main_menu, "Профиль", "Redeem"):
                    return
                
                # 2. Profile screen ke response buttons se 'Промокод' par click karein
                second_menu = await wait_for_buttons(account_num, conv, "Redeem")
                if not second_menu or not await click_button(account_num, second_menu, "Промокод", "Redeem"):
                    return
                
                # 3. Input text prompt ke liye thoda wait karke promo code send karein
                await wait_for_buttons(account_num, conv, "Redeem", timeout=5)
                await random_delay()
                await conv.send_message(promo_code)
                
                last_redeemed[account_num] = promo_code
                print(f"✅ [{account_num}][Redeem] Log: Successfully submitted promo '{promo_code}'")
        except Exception as e:
            print(f"❌ [{account_num}][Redeem] Execution Error: {e}")

# ==========================================
# TIMED LOOP (10 MINUTE)
# ==========================================
async def clicker_loop(client, account_num):
    # Accounts ke beech collision/load na ho isliye starting staggered delay
    await asyncio.sleep(account_num * 2.5) 
    while True:
        await perform_clicker_task(client, account_num)
        await asyncio.sleep(600)

# ==========================================
# ACCOUNT DISPATCHER
# ==========================================
async def run_account(session_string, account_num):
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    try:
        await client.start()
        me = await client.get_me()
        print(f"🟩 [{account_num}] Log: {me.first_name} (@{me.username or 'NoUser'}) Connected.")
        
        conversation_locks[account_num] = asyncio.Lock()
        last_redeemed[account_num] = None
        processing_promos[account_num] = set()

        # Listen to target channel events instantly
        @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
        async def handler(event):
            try:
                # Event message ko full process ke liye function mein bhejte hain
                promo = extract_promocode(event.message)
                
                if promo and promo not in processing_promos[account_num]:
                    processing_promos[account_num].add(promo)
                    # Har account ko sequence delays ke sath deploy karein taaki target bot rate limit na kare
                    await asyncio.sleep(account_num * 0.5)
                    asyncio.create_task(perform_interaction(client, account_num, promo))
            except Exception as ev_err:
                print(f"❌ [{account_num}][Event] Log: Handler error: {ev_err}")

        # Start 10-minute click loop background task
        asyncio.create_task(clicker_loop(client, account_num))
        await client.run_until_disconnected()

    except Exception as e:
        print(f"🟥 [{account_num}] Log: Runtime Error: {e}")

