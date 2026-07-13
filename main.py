import asyncio
import os
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType

# API credentials
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
target_channel = os.getenv("TARGET_CHANNEL")
bot_username = "patrickstarsrobot"

# Sessions loading
sessions = [os.getenv(f"SESSION_{i}") for i in range(1, 14) if os.getenv(f"SESSION_{i}")]

# 'in_memory' use kiya hai taaki koi purana cache error na aaye
clients = [Client(f"session_{i}", api_id=api_id, api_hash=api_hash, session_string=s, in_memory=True) for i, s in enumerate(sessions)]

async def claim_code(client, code):
    try:
        # Button click simulate
        async for msg in client.get_chat_history(bot_username, limit=1):
            if msg.reply_markup:
                for row in msg.reply_markup.inline_keyboard:
                    for button in row:
                        if "Промокод" in button.text:
                            await client.request_callback_answer(chat_id=bot_username, message_id=msg.id, callback_data=button.callback_data)
                            await asyncio.sleep(0.2)
        
        # Send Code
        await client.send_message(bot_username, code)
        print(f"[{client.name}] Code {code} successfully sent!")
    except Exception as e:
        print(f"[{client.name}] Error: {e}")

@Client.on_message(filters.chat(int(target_channel) if target_channel.lstrip('-').isdigit() else target_channel) & filters.incoming)
async def monitor(client, message):
    if message.text and message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.SPOILER:
                code = message.text[entity.offset : entity.offset + entity.length]
                print(f"Code Found: {code}. Starting sequence...")
                tasks = [claim_code(c, code) for c in clients]
                await asyncio.gather(*tasks)

async def main():
    for app in clients:
        await app.start()
        print(f"[{app.name}] Account started.")
            
    print("Bot is ready and listening...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

