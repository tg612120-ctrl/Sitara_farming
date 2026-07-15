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
TARGET_RESPONSE = "✨ Для получения звезд на твой баланс введи промокод:"

async def start_userbot(session_str, account_num):
    client = TelegramClient(StringSession(session_str.strip()), API_ID, API_HASH)
    await client.start()
    print(f"✅ Account {account_num} is online")

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def spoiler_handler(event):
        # 1. Extract the spoiler
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if not spoiler_text: return
        print(f"📌 [{account_num}] Spoiler found: {spoiler_text}")

        try:
            # FIX: Using direct method instead of get_full_chat
            bot_entity = await client.get_input_entity(TARGET_BOT)
            pinned_msg = await client.get_messages(bot_entity, ids=0)
            
            if pinned_msg and pinned_msg.buttons:
                await pinned_msg.click(0)
                print(f"🔘 [{account_num}] Pin message clicked.")

                async with client.conversation(TARGET_BOT) as conv:
                    # Wait for menu message
                    menu_msg = await conv.wait_event(events.NewMessage(chats=TARGET_BOT), timeout=15)
                    if menu_msg and menu_msg.message.buttons:
                        for row in menu_msg.message.buttons:
                            for button in row:
                                if "Промокод" in button.text:
                                    await button.click()
                                    print(f"🔘 [{account_num}] 'Промокод' button clicked.")
                                    break
                    
                    # Wait for target response
                    final_response = await conv.wait_event(events.NewMessage(chats=TARGET_BOT), timeout=15)
                    if final_response and TARGET_RESPONSE in final_response.message.text:
                        await conv.send_message(spoiler_text)
                        print(f"🚀 [{account_num}] Code {spoiler_text} successfully sent!")
                        
        except Exception as e:
            print(f"❌ [{account_num}] Error: {e}")

    return client

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: 
        print("SESSION_STRINGS variable not set!")
        return
        
    print(f"🚀 Starting with {len(SESSION_STRINGS)} accounts...")
    await asyncio.gather(*[start_userbot(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)])
    # Keep the bot running
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())

