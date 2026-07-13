import asyncio
import os
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
target_channel = int(os.getenv("TARGET_CHANNEL"))
bot_username = "patrickstarsrobot"

sessions = [os.getenv(f"SESSION_{i}") for i in range(1, 14) if os.getenv(f"SESSION_{i}")]
clients = [Client(f"session_{i}", api_id=api_id, api_hash=api_hash, session_string=s, in_memory=True) for i, s in enumerate(sessions)]

async def execute_flow(client, code):
    try:
        # 1. DM mein jao aur "Промокод" button click karo
        async for msg in client.get_chat_history(bot_username, limit=3):
            if msg.reply_markup:
                for row in msg.reply_markup.inline_keyboard:
                    for button in row:
                        if "Промокод" in button.text:
                            await client.request_callback_answer(chat_id=bot_username, message_id=msg.id, callback_data=button.callback_data)
                            print(f"[{client.name}] Step 1: Button Clicked.")
                            break
        
        # 2. 5 seconds ka wait (Bot ke naye message ke liye)
        print(f"[{client.name}] Waiting 5 seconds for bot response...")
        await asyncio.sleep(5)
        
        # 3. Code bhej do
        await client.send_message(bot_username, code)
        print(f"[{client.name}] Step 2: Code {code} sent.")
        
    except Exception as e:
        print(f"[{client.name}] Error in flow: {e}")

@Client.on_message(filters.chat(target_channel) & filters.incoming)
async def monitor(client, message):
    if message.text and message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.SPOILER:
                code = message.text[entity.offset : entity.offset + entity.length]
                print(f"Code Found: {code}. Starting flow...")
                tasks = [execute_flow(c, code) for c in clients]
                await asyncio.gather(*tasks)

async def main():
    for app in clients:
        await app.start()
    print("Bot is ready and listening...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

