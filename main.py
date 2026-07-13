import asyncio
import os
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
target_channel = os.getenv("TARGET_CHANNEL")
bot_username = "patrickstarsrobot"

sessions = [os.getenv(f"SESSION_{i}") for i in range(1, 14) if os.getenv(f"SESSION_{i}")]
clients = [Client(f"session_{i}", api_id=api_id, api_hash=api_hash, session_string=s) for i, s in enumerate(sessions)]

# Global variable to store resolved chat ID
resolved_chat_id = None

async def claim_code(client, code):
    try:
        # 1. Open Chat
        chat = await client.get_chat(bot_username)
        
        # 2. Button click simulate (Click 'Промокод')
        # Humesha latest message mein button hota hai
        async for msg in client.get_chat_history(bot_username, limit=1):
            if msg.reply_markup:
                for row in msg.reply_markup.inline_keyboard:
                    for button in row:
                        if "Промокод" in button.text:
                            await client.request_callback_answer(chat_id=bot_username, message_id=msg.id, callback_data=button.callback_data)
                            await asyncio.sleep(1) # Thoda wait
                            
        # 3. Send Code
        await client.send_message(bot_username, code)
        print(f"[{client.name}] Code {code} successfully claimed!")
    except Exception as e:
        print(f"[{client.name}] Error in claiming: {e}")

@Client.on_message(filters.chat(lambda _, m: m.chat.id == resolved_chat_id) & filters.incoming)
async def monitor(client, message):
    print(f"DEBUG: Message received in channel: {message.text[:20]}...") # Ye check karne ke liye ki bot sun raha hai
    
    if message.text and message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.SPOILER:
                code = message.text[entity.offset : entity.offset + entity.length]
                print(f"Code Found: {code}. Starting sequence...")
                
                # Sabhi clients se parallel start
                tasks = [claim_code(c, code) for c in clients]
                await asyncio.gather(*tasks)

async def main():
    global resolved_chat_id
    for app in clients:
        await app.start()
        # Resolve ID
        try:
            chat = await app.get_chat(target_channel)
            resolved_chat_id = chat.id
            print(f"[{app.name}] Monitoring active for: {chat.title} (ID: {chat.id})")
        except Exception as e:
            print(f"Error resolving channel {target_channel}: {e}")
            
    print("Bot is ready and listening...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

