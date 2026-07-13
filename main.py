import asyncio
import os
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
target_channel = os.getenv("TARGET_CHANNEL") # Link ya ID
bot_username = "patrickstarsrobot"

sessions = [os.getenv(f"SESSION_{i}") for i in range(1, 14) if os.getenv(f"SESSION_{i}")]
clients = [Client(f"session_{i}", api_id=api_id, api_hash=api_hash, session_string=s) for i, s in enumerate(sessions)]

async def claim_sequence(client, code):
    try:
        # 1. Bot ke saath chat history lein
        chat = await client.get_chat(bot_username)
        
        # 2. "Промокод" button dhoondhein aur click karein
        # (Ye button usually recent message mein hota hai)
        async for msg in client.get_chat_history(bot_username, limit=1):
            if msg.reply_markup:
                for row in msg.reply_markup.inline_keyboard:
                    for button in row:
                        if "Промокод" in button.text:
                            await client.request_callback_answer(chat_id=bot_username, message_id=msg.id, callback_data=button.callback_data)
                            await asyncio.sleep(0.3)
        
        # 3. Code bhejein
        await client.send_message(bot_username, code)
        print(f"[{client.name}] Code {code} sent!")
    except Exception as e:
        print(f"[{client.name}] Error: {e}")

@Client.on_message(filters.chat(target_channel) & filters.incoming)
async def monitor(client, message):
    if message.text and message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.SPOILER:
                code = message.text[entity.offset : entity.offset + entity.length]
                print(f"Code Found: {code}. Claiming with all accounts...")
                
                # Sabhi accounts se ek saath claim start karein (Fast speed)
                tasks = [claim_sequence(c, code) for c in clients]
                await asyncio.gather(*tasks)

async def main():
    for app in clients:
        await app.start()
        # Ensure joined
        try: await app.join_chat(target_channel)
        except: pass
    print("Bot is ready and listening...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

