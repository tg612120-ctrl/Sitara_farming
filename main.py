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
        # 1. Spoiler extract karo
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if not spoiler_text: return
        print(f"📌 [{account_num}] स्पॉइलर मिला: {spoiler_text}")

        try:
            async with client.conversation(TARGET_BOT) as conv:
                # 1. PIN Message click karo
                full_chat = await client.get_full_chat(TARGET_BOT)
                pinned_msg = await client.get_messages(TARGET_BOT, ids=full_chat.full_chat.pinned_msg_id)
                
                if pinned_msg and pinned_msg.buttons:
                    # Pin message ka main button click karo
                    await pinned_msg.click(0)
                    print(f"🔘 [{account_num}] Pin message clicked.")

                    # 2. Menu message ka wait karo
                    menu_msg = await conv.wait_event(events.NewMessage(chats=TARGET_BOT), timeout=15)
                    
                    # 3. "Промокод" button dhundo aur click karo
                    if menu_msg.message.buttons:
                        for row in menu_msg.message.buttons:
                            for button in row:
                                if "Промокод" in button.text:
                                    await button.click()
                                    print(f"🔘 [{account_num}] 'Промокод' button clicked.")
                                    break
                    
                    # 4. Target response ka wait karo
                    final_response = await conv.wait_event(events.NewMessage(chats=TARGET_BOT), timeout=15)
                    
                    if TARGET_RESPONSE in final_response.message.text:
                        await conv.send_message(spoiler_text)
                        print(f"🚀 [{account_num}] Code {spoiler_text} successfully sent!")
                        
        except Exception as e:
            print(f"❌ [{account_num}] Error: {e}")

    return client

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]:
        print("SESSION_STRINGS variable set nahi hai!")
        return

    print(f"🚀 कुल {len(SESSION_STRINGS)} अकाउंट्स के साथ स्टार्ट हो रहा है...")
    tasks = [start_userbot(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)]
    await asyncio.gather(*tasks)
    
    # Bot ko hamesha chalate rakho
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())

