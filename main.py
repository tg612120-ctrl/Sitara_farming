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

# Global dictionary to store clients
clients = {}

async def run_account(session_str, account_num):
    # Session string ko trim karna zaroori hai
    session_str = session_str.strip()
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    
    try:
        await client.start()
        print(f"✅ Account {account_num} is online")
        clients[account_num] = client
    except Exception as e:
        print(f"❌ [{account_num}] Start error: {e}")
        return

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def spoiler_handler(event):
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if spoiler_text:
            print(f"📌 [{account_num}] Spoiler detected: {spoiler_text}")
            await perform_interaction(client, account_num, spoiler_text)

    # Client ko run hone do
    await client.run_until_disconnected()

async def perform_interaction(client, account_num, spoiler_text):
    try:
        # Conversation timeout kam rakha hai taaki lock na ho
        async with client.conversation(TARGET_BOT, timeout=15) as conv:
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
            print(f"🚀 [{account_num}] Code {spoiler_text} sent!")
            
    except Exception as e:
        print(f"❌ [{account_num}] Interaction error: {e}")

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: 
        print("SESSION_STRINGS not set!")
        return
        
    # Gather all accounts
    tasks = [run_account(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

