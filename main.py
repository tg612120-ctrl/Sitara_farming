import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntitySpoiler

# API credentials
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRINGS = os.getenv("SESSION_STRINGS", "").split(",")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_BOT = 'patrickstarsrobot'

async def start_userbot(session_str, account_num):
    client = TelegramClient(StringSession(session_str.strip()), API_ID, API_HASH)
    await client.start()
    print(f"✅ Account {account_num} is online")

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def spoiler_handler(event):
        # 1. Sirf tabhi kaam karo jab spoiler ho
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if not spoiler_text: return
        print(f"📌 [{account_num}] Spoiler detected: {spoiler_text}")

        # 2. Spoiler milte hi ab flow shuru karo
        try:
            async with client.conversation(TARGET_BOT) as conv:
                # Flow step 1: /start
                await conv.send_message('/start')
                await conv.get_response() # Bot ka start msg clear kiya
                
                # Flow step 2: Click '👤 профиль'
                # Note: Agar button command message se trigger hota hai to send_message use karo
                await conv.send_message("👤 профиль") 
                profile_menu = await conv.get_response()
                
                # Flow step 3: Click '🎫 промокод'
                found = False
                if profile_menu.buttons:
                    for row in profile_menu.buttons:
                        for button in row:
                            if "🎫 промокод" in button.text:
                                await button.click()
                                found = True
                                break
                
                # Flow step 4: Bot ke prompt message ka wait karo aur turant code bhejo
                if found:
                    await conv.get_response() # Bot ka "Enter promo code" wala message
                    await conv.send_message(spoiler_text)
                    print(f"🚀 [{account_num}] Code {spoiler_text} sent successfully!")
                        
        except Exception as e:
            print(f"❌ [{account_num}] Flow error: {e}")

    return client

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: return
    print(f"🚀 Waiting for spoilers...")
    await asyncio.gather(*[start_userbot(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)])
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())

