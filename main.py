import asyncio
import os
from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
# ID ya Username string mein hi rahega, resolution hum handle karenge
target_channel = os.getenv("TARGET_CHANNEL")
bot_username = "patrickstarsrobot"

sessions = [os.getenv(f"SESSION_{i}") for i in range(1, 14) if os.getenv(f"SESSION_{i}")]
clients = [Client(f"session_{i}", api_id=api_id, api_hash=api_hash, session_string=s) for i, s in enumerate(sessions)]

# Resolved ID ko store karne ke liye
resolved_chat_id = None

async def claim_code(client, code):
    try:
        # Button click simulate
        async for msg in client.get_chat_history(bot_username, limit=1):
            if msg.reply_markup:
                for row in msg.reply_markup.inline_keyboard:
                    for button in row:
                        if "Промокод" in button.text:
                            await client.request_callback_answer(chat_id=bot_username, message_id=msg.id, callback_data=button.callback_data)
                            await asyncio.sleep(0.5) 
                            
        # Send Code
        await client.send_message(bot_username, code)
        print(f"[{client.name}] Code {code} sent!")
    except Exception as e:
        print(f"[{client.name}] Error: {e}")

@Client.on_message(filters.chat(lambda _, m: m.chat.id == resolved_chat_id) & filters.incoming)
async def monitor(client, message):
    if message.text and message.entities:
        for entity in message.entities:
            if entity.type == MessageEntityType.SPOILER:
                code = message.text[entity.offset : entity.offset + entity.length]
                print(f"Code Found: {code}. Claiming...")
                tasks = [claim_code(c, code) for c in clients]
                await asyncio.gather(*tasks)

async def main():
    global resolved_chat_id
    for app in clients:
        await app.start()
        # Numeric ID ya Username ko resolve karna
        try:
            # Agar ID -100 se shuru ho rahi hai, toh use integer mein convert karke resolve karein
            chat_identifier = int(target_channel) if target_channel.lstrip('-').isdigit() else target_channel
            chat = await app.get_chat(chat_identifier)
            resolved_chat_id = chat.id
            print(f"[{app.name}] Successfully monitoring: {chat.title} (ID: {chat.id})")
            break # Ek baar resolve ho gaya toh kaafi hai
        except Exception as e:
            print(f"[{app.name}] Error resolving {target_channel}: {e}")
            
    print("Bot is ready and listening...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
