import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntitySpoiler

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRINGS = os.getenv("SESSION_STRINGS", "").split(",")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_BOT = 'patrickstarsrobot'

async def perform_interaction(client, account_num, spoiler_text):
    try:
        # Timeout 30s rakha hai taaki heavy load mein bhi bot wait kar sake
        async with client.conversation(TARGET_BOT, timeout=30) as conv:
            await conv.send_message('/start')
            
            # 1. Menu wait (Jab tak message na aaye, tab tak wait karega)
            start_resp = await conv.get_response()
            
            # Click 'Профиль'
            if start_resp and start_resp.buttons:
                for row in start_resp.buttons:
                    for button in row:
                        if "Профиль" in button.text:
                            await button.click()
                            print(f"🔘 [{account_num}] Clicked: Профиль")
                            break
            
            # 2. Promo menu wait (Immediate response trigger)
            promo_menu = await conv.get_response()
            
            # Click 'Промокод'
            clicked_promo = False
            if promo_menu and promo_menu.buttons:
                for row in promo_menu.buttons:
                    for button in row:
                        if "Промокод" in button.text:
                            await button.click()
                            clicked_promo = True
                            print(f"🔘 [{account_num}] Clicked: Промокод")
                            break
            
            if not clicked_promo:
                print(f"❌ [{account_num}] 'Промокод' button nahi mila!")
                return
            
            # 3. Final Step: Spoiler bhejo
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
            # Background task mein chalao taaki handler free rahe
            asyncio.create_task(perform_interaction(client, account_num, spoiler_text))

    await client.run_until_disconnected()

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: return
    await asyncio.gather(*[run_account(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)])

if __name__ == '__main__':
    asyncio.run(main())

