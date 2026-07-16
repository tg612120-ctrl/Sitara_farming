hereimport os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntitySpoiler

# Configurations
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRINGS = os.getenv("SESSION_STRINGS", "").split(",")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_BOT = 'patrickstarsrobot'

async def perform_interaction(client, account_num, spoiler_text):
    try:
        async with client.conversation(TARGET_BOT, timeout=40) as conv:
            await conv.send_message('/start')
            
            # 1. Main Menu (Wait)
            start_resp = await conv.get_response()
            
            # DEBUGGING: Buttons ka layout check karne ke liye
            if start_resp.buttons:
                print(f"DEBUG [{account_num}] Layout check:")
                for r_idx, row in enumerate(start_resp.buttons):
                    print(f"DEBUG [{account_num}] Row {r_idx}: {[b.text for b in row]}")
            
            # Click 'Профиль' (Index based - adjust if needed from logs)
            # Row 2, Column 0 ke hisaab se try kar rahe hain
            if start_resp.buttons and len(start_resp.buttons) > 2:
                await start_resp.buttons[2][0].click()
                print(f"🔘 [{account_num}] Clicked Profile at [2][0]")
            else:
                print(f"❌ [{account_num}] Menu buttons structure nahi mila!")
                return

            # 2. Promo Menu (Wait)
            promo_menu = await conv.get_response()
            
            # Click 'Промокод' (Adjust index based on logs)
            if promo_menu.buttons and len(promo_menu.buttons) > 1:
                await promo_menu.buttons[1][0].click()
                print(f"🔘 [{account_num}] Clicked Promo at [1][0]")
            else:
                print(f"❌ [{account_num}] Promo menu buttons nahi mile!")
                return
            
            # 3. Final Step: Spoiler code bhejo
            await conv.get_response()
            await conv.send_message(spoiler_text)
            print(f"🚀 [{account_num}] Success: {spoiler_text} sent!")
            
    except Exception as e:
        print(f"❌ [{account_num}] Interaction error: {e}")

async def run_account(session_str, account_num):
    client = TelegramClient(StringSession(session_str.strip()), API_ID, API_HASH)
    try:
        await client.start()
        print(f"✅ Account {account_num} is online")
        channel = await client.get_input_entity(SOURCE_CHANNEL)
    except Exception as e:
        print(f"❌ [{account_num}] Setup error: {e}")
        return

    @client.on(events.NewMessage(chats=channel))
    async def spoiler_handler(event):
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if spoiler_text:
            print(f"📌 [{account_num}] Spoiler detected: {spoiler_text}")
            asyncio.create_task(perform_interaction(client, account_num, spoiler_text))

    await client.run_until_disconnected()

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: return
    await asyncio.gather(*[run_account(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)])

if __name__ == '__main__':
    asyncio.run(main())
