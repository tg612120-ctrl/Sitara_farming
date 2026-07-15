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

async def start_userbot(session_str, account_num):
    client = TelegramClient(StringSession(session_str.strip()), API_ID, API_HASH)
    await client.start()
    print(f"✅ Account {account_num} is online")

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def spoiler_handler(event):
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if not spoiler_text: return
        print(f"📌 [{account_num}] Spoiler detected: {spoiler_text}")

        try:
            # Conversation ko 'with' block se bahar access karo ya 
            # check karo ki koi existing conversation to nahi
            async with client.conversation(TARGET_BOT, timeout=20) as conv:
                await conv.send_message('/start')
                start_resp = await conv.get_response()
                
                # Click 'Профиль'
                if start_resp.buttons:
                    for row in start_resp.buttons:
                        for button in row:
                            if "Профиль" in button.text:
                                await button.click()
                                break
                
                # Click 'Промокод'
                promo_menu = await conv.get_response()
                if promo_menu.buttons:
                    for row in promo_menu.buttons:
                        for button in row:
                            if "Промокод" in button.text:
                                await button.click()
                                break
                
                # Send spoiler
                await conv.get_response()
                await conv.send_message(spoiler_text)
                print(f"🚀 [{account_num}] Code {spoiler_text} sent!")
                        
        except asyncio.TimeoutError:
            print(f"❌ [{account_num}] Timeout error: Bot slow hai.")
        except Exception as e:
            print(f"❌ [{account_num}] Error: {e}")

    return client

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: return
    await asyncio.gather(*[start_userbot(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)])
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())

