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

# Source channel direct code mein add kar diya hai
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

async def wait_for_buttons(account_num, conv, task_name, timeout=15):
    """Buttons ka wait karta hai aur error aane par Railway logs mein show karta hai"""
    try:
        msg = await conv.get_response(timeout=timeout)
        if msg:
            if msg.buttons:
                return msg
            else:
                print(f"⚠️ [{account_num}][{task_name}] Log: Bot replied but NO buttons found on message: '{msg.raw_text[:30]}...'")
        else:
            print(f"⚠️ [{account_num}][{task_name}] Log: Bot returned an empty response.")
    except asyncio.TimeoutError:
        print(f"⏰ [{account_num}][{task_name}] Log: Timeout! Target bot did not reply within {timeout} seconds.")
    except Exception as e:
        print(f"❌ [{account_num}][{task_name}] Log: Error while waiting for response: {e}")
    return None

async def click_button(account_num, message, keyword, task_name):
    """Button click karta hai aur keyword match na hone par explicit logs generate karta hai"""
    if not message:
        print(f"⚠️ [{account_num}][{task_name}] Log: Cannot click button because message object is None.")
        return False
    if not message.buttons:
        print(f"⚠️ [{account_num}][{task_name}] Log: Message has no buttons to click. Text: '{message.raw_text[:40]}'")
        return False
        
    keyword = keyword.lower()
    available_buttons = []
    
    for row in message.buttons:
        for button in row:
            available_buttons.append(button.text)
            if keyword in button.text.lower():
                await random_delay()
                try:
                    await button.click()
                    print(f"🎯 [{account_num}][{task_name}] Log: Successfully clicked button '{button.text}'")
                    return True
                except Exception as e:
                    print(f"❌ [{account_num}][{task_name}] Log: Failed to click button '{button.text}': {e}")
                    return False
                    
    # Agar loop khatam ho gaya aur button nahi mila
    print(f"🔍 [{account_num}][{task_name}] Log: Button with keyword '{keyword}' NOT found! Available buttons: {available_buttons}")
    return False

def extract_promocode(text):
    if not text:
        return None
    matches = re.findall(r"\b[A-Za-z0-9_]{6,}\b", text)
    for match in matches:
        if match.lower() not in ["кликер", "профиль", "промокод", "start", "help"]:
            return match
    return None

def solve_math(text):
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
    lock = conversation_locks.get(account_num)
    if not lock: return
    
    async with lock:
        try:
            print(f"🔄 [{account_num}][Clicker] Log: Starting 10-minute task...")
            async with client.conversation(TARGET_BOT, timeout=45) as conv:
                await conv.send_message("/start")
                
                menu = await wait_for_buttons(account_num, conv, "Clicker")
                if not menu or not await click_button(account_num, menu, "Кликер", "Clicker"):
                    return

                response = await wait_for_buttons(account_num, conv, "Clicker")
                if response:
                    if "=" in response.raw_text or any(op in response.raw_text for op in ["+", "-", "*"]):
                        ans = solve_math(response.raw_text)
                        if ans is not None:
                            print(f"🔢 [{account_num}][Clicker] Log: Captcha Math detected: {response.raw_text.strip()} -> Answer: {ans}")
                            await click_button(account_num, response, str(ans), "Clicker")
                        else:
                            print(f"⚠️ [{account_num}][Clicker] Log: Could not parse math expression from text: '{response.raw_text}'")
                    else:
                        print(f"ℹ️ [{account_num}][Clicker] Log: Interface updated but no math captcha found. Text: '{response.raw_text[:40]}'")
        except Exception as e:
            print(f"❌ [{account_num}][Clicker] Critical Error: {e}")

async def perform_interaction(client, account_num, promo_code):
    if last_redeemed.get(account_num) == promo_code:
        return
        
    lock = conversation_locks.get(account_num)
    if not lock: return
    
    async with lock:
        try:
            print(f"🚀 [{account_num}][Redeem] Log: Found code '{promo_code}', starting redeem process...")
            async with client.conversation(TARGET_BOT, timeout=60) as conv:
                await conv.send_message("/start")
                
                main_menu = await wait_for_buttons(account_num, conv, "Redeem")
                if not main_menu or not await click_button(account_num, main_menu, "Профиль", "Redeem"):
                    return
                
                second_menu = await wait_for_buttons(account_num, conv, "Redeem")
                if not second_menu or not await click_button(account_num, second_menu, "Промокод", "Redeem"):
                    return
                
                # Input prompt text aane ka wait karein
                await wait_for_buttons(account_num, conv, "Redeem", timeout=5)
                await random_delay()
                await conv.send_message(promo_code)
                
                last_redeemed[account_num] = promo_code
                print(f"✅ [{account_num}][Redeem] Log: Promo '{promo_code}' sent to bot dashboard.")
        except Exception as e:
            print(f"❌ [{account_num}][Redeem] Critical Error: {e}")

# ==========================================
# CLICKER LOOP (10 MINUTE)
# ==========================================
async def clicker_loop(client, account_num):
    await asyncio.sleep(account_num * 2) 
    while True:
        await perform_clicker_task(client, account_num)
        await asyncio.sleep(600)

# ==========================================
# ACCOUNT RUNNER
# ==========================================
async def run_account(session_string, account_num):
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
    try:
        await client.start()
        me = await client.get_me()
        print(f"🟩 [{account_num}] Log: {me.first_name} (@{me.username or 'NoUser'}) Connected successfully.")
        
        conversation_locks[account_num] = asyncio.Lock()
        last_redeemed[account_num] = None
        processing_promos[account_num] = set()

        @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
        async def handler(event):
            try:
                text = event.message.raw_text or ""
                promo = extract_promocode(text)
                
                if promo and promo not in processing_promos[account_num]:
                    processing_promos[account_num].add(promo)
                    await asyncio.sleep(account_num * 0.4)
                    asyncio.create_task(perform_interaction(client, account_num, promo))
            except Exception as ev_err:
                print(f"❌ [{account_num}][Event] Log: Handler processing error: {ev_err}")

        asyncio.create_task(clicker_loop(client, account_num))
        await client.run_until_disconnected()

    except Exception as e:
        print(f"🟥 [{account_num}] Log: Serious Account Runtime Error: {e}")

# ==========================================
# MAIN EXECUTION
# ==========================================
async def main():
    if not SESSION_STRINGS:
        print("🟥 [System] Log: SESSION_STRINGS environment variable is empty!")
        return
    if not API_ID or not API_HASH:
        print("🟥 [System] Log: API_ID or API_HASH variables are missing!")
        return
        
    print(f"⚙️ [System] Log: Starting Userbot Application with {len(SESSION_STRINGS)} accounts...")
    tasks = [asyncio.create_task(run_account(s, i+1)) for i, s in enumerate(SESSION_STRINGS)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

