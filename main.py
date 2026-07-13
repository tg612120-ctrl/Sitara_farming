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
clients = [Client(f"user_{i}", api_id=api_id, api_hash=api_hash, session_string=s) for i, s in enumerate(sessions)]

async def claim_code(client, code):
    try:
        await client.send_message(bot_username, "Промокод")
        await asyncio.sleep(0.5) 
        await client.send_message(bot_username, code)
        print(f"[{client.name}] Code {code} successfully sent!")
    except Exception as e:
        print(f"Error for {client.name}: {e}")

@Client.on_message(filters.chat(target_channel) & filters.incoming)
async def monitor(client, message):
    if message.text and message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.SPOILER:
                code = message.text[entity.offset : entity.offset + entity.length]
                print(f"Code Found: {code}. Starting sequence...")
                
                # Sequence Logic: 1 ID, then 2 sec pause, then next ID
                for c in clients:
                    await claim_code(c, code)
                    await asyncio.sleep(2) # 2 seconds ka safe gap

async def main():
    for app in clients:
        await app.start()
    print("Bot is ready and listening...")
    # Sahi tareeka bot ko active rakhne ka
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

