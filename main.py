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

async def perform_interaction(client, account_num, spoiler_text):
    try:
        async with client.conversation(TARGET_BOT, timeout=30) as conv:
            await conv.send_message('/start')
            
            # Helper function: Buttons mein emoji-safe search
            def get_button(buttons, search_text):
                if not buttons: return None
                for row in buttons:
                    for button in row:
                        clean_text = "".join(c for c in button.text if c.isalpha() or c.isdigit())
                        if search_text in clean_text:
                            return button
                return None

            # 1. Start response ka wait
            start_resp = await conv.get_response()
            btn_profile = get_button(start_resp.buttons, "Профиль")
            
            if btn_profile:
                await asyncio.sleep(0.5) # Bot ko saans lene do
                await btn_profile.click()
                print(f"🔘 [{account_num}] Clicked: {btn_profile.text}")
            else:
                print(f"❌ [{account_num}] 'Профиль' button nahi mila!")
                return

            # 2. Promo menu ka wait
            promo_menu = await conv.get_response()
            btn_promo = get_button(promo_menu.buttons, "Промокод")
            
            if btn_promo:
                await asyncio.sleep(0.5)
                await btn_promo.click()
                print(f"🔘 [{account_num}] Clicked: {btn_promo.text}")
            else:
                print(f"❌ [{account_num}] 'Промокод' button nahi mila!")
                return
            
            # 3. Final: Spoiler code bhejo
            await conv.get_response()
            await conv.send_message(spoiler_text)
            print(f"🚀 [{account_num}] Success: {spoiler_text} sent!")
            
    except Exception as e:
        print(f"❌ [{account_num}] Interaction error: {e}")

async def run_account(session_str, account_num):
    # StringSession ko handle karna
    client = TelegramClient(StringSession(session_str.strip()), API_ID, API_HASH)
    try:
        await client.start()
        print(f"✅ Account {account_num} is online")
        channel = await client.get_input_entity(SOURCE_CHANNEL)
    except Exception as e:
        print(f"❌ [{account_num}] Setup error: {e}")
        return

    @client.on(events.NewMessage(chats=channel))
    async def spoiler_handler(event):
        spoiler_text = None
        if event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntitySpoiler):
                    # Spoiler ka text nikaalo
                    spoiler_text = event.raw_text[entity.offset:entity.offset+entity.length]
        
        if spoiler_text:
            print(f"📌 [{account_num}] Spoiler detected: {spoiler_text}")
            # Background task taaki bot hang na ho
            asyncio.create_task(perform_interaction(client, account_num, spoiler_text))

    await client.run_until_disconnected()

async def main():
    if not SESSION_STRINGS or SESSION_STRINGS == [""]: return
    await asyncio.gather(*[run_account(s, i) for i, s in enumerate(SESSION_STRINGS, start=1)])

if __name__ == '__main__':
    asyncio.run(main())

