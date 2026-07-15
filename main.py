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
        async with client.conversation(TARGET_BOT, timeout=20) as conv:
            await conv.send_message('/start')
            start_resp = await conv.get_response()
            
            # Click 'Профиль'
            if start_resp and start_resp.buttons:
                for row in start_resp.buttons:
                    for button in row:
                        if "Профиль" in button.text:
                            await button.click()
                            break
            
            # Click 'Промокод'
            promo_menu = await conv.get_response()
            if promo_menu and promo_menu.buttons:
                for row in promo_menu.buttons:
                    for button in row:
                        if "Промокод" in button.text:
                            await button.click()
                            break
            
            # Send spoiler
            await conv.get_response()
            await conv.send_message(spoiler_text)
            print(f"🚀 [{account_num}] Code {spoiler_text} sent successfully!")
            
    except Exception as e:
        print(f"❌ [{account_num}] Interaction error: {e}")

async def run_account(session_str, account_num):
    client = TelegramClient(StringSession(session_str.strip()), API_ID, API_HASH)
    
    try:
        await client.start()
        print(f"✅ Account {account_num} is online")
        
        # Channel entity resolve karna zaroori hai taaki event filter sahi chale
        channel = await client.get_input_entity(SOURCE_CHANNEL)
        print(f"🔍 [{account_num}] Monitoring channel: {SOURCE_CHANNEL}")
    except Exception as e:
        print(f"❌ [{account_num}] Start/Entity error: {e}")
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
            # Background task mein interaction chalao taaki bot block na ho
            asyncio.create_task(perform_interaction(client, account_num, spoiler_text))
        else:
            # Ye line debug ke liye hai, agar spoiler nahi mil raha toh pata chalega
            print(f"📩 [{account_num}] New message received, but no spoiler found.")

    await client.run_until_disconnected()

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: 
        print("SESSION_STRINGS not set!")
        return
        
    tasks = [run_account(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

