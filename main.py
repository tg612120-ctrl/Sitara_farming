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
    print(f"✅ अकाउंट {account_num} ऑनलाइन है")

    @client.on(events.NewMessage(chats=SOURCE_CHANNEL))
    async def spoiler_handler(event):
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if not spoiler_text: return
        print(f"📌 स्पॉइलर मिला: {spoiler_text}")

        try:
            async with client.conversation(TARGET_BOT) as conv:
                # 1. PIN Message click karo
                full_chat = await client.get_full_chat(TARGET_BOT)
                pinned_msg = await client.get_messages(TARGET_BOT, ids=full_chat.full_chat.pinned_msg_id)
                
                if pinned_msg and pinned_msg.buttons:
                    # Pin message ka button click karo
                    await pinned_msg.click(0) # Pin message ka main button
                    print("🔘 Pin message clicked.")

                    # 2. Ab wait karo us naye message ka jisme buttons hain
                    menu_msg = await conv.wait_event(events.NewMessage(chats=TARGET_BOT), timeout=10)
                    
                    # 3. Naye message mein "Промокод" button dhundo aur click karo
                    if menu_msg.message.buttons:
                        for row in menu_msg.message.buttons:
                            for button in row:
                                if "Промокод" in button.text:
                                    await button.click()
                                    print("🔘 'Промокод' button clicked in menu.")
                                    break
                    
                    # 4. Ab "TARGET_RESPONSE" ka wait karo
                    final_response = await conv.wait_event(events.NewMessage(chats=TARGET_BOT), timeout=10)
                    
                    if TARGET_RESPONSE in final_response.message.text:
                        await conv.send_message(spoiler_text)
                        print(f"🚀 Code {spoiler_text} successfully sent!")
                        
        except Exception as e:
            print(f"❌ Error: {e}")

    await client.run_until_disconnected()

async def main():
    tasks = [start_userbot(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

