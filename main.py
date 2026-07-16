import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntitySpoiler

# ==========================
# CONFIG
# ==========================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

SESSION_STRINGS = [
    s.strip() for s in os.getenv("SESSION_STRINGS", "").split(",") if s.strip()
]

SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_BOT = "patrickstarsrobot"


# ==========================
# HELPERS
# ==========================

async def wait_for_buttons(conv, max_messages=8):
    """
    Wait until a message with buttons arrives.
    """
    for _ in range(max_messages):
        msg = await conv.get_response()

        print("\n==========================")
        print(msg.raw_text)

        if msg.buttons:
            print("Buttons:")
            for row in msg.buttons:
                print([btn.text for btn in row])
            print("==========================\n")
            return msg

    return None


async def click_button_by_text(message, keyword):
    """
    Find button by partial text and click it.
    """
    if not message.buttons:
        return False

    keyword = keyword.lower()

    for row in message.buttons:
        for button in row:
            if keyword in button.text.lower():
                await button.click()
                return True

    return False


# ==========================
# MAIN INTERACTION
# ==========================

async def perform_interaction(client, account_num, spoiler_text):
    try:
        async with client.conversation(TARGET_BOT, timeout=60) as conv:

            print(f"\n[{account_num}] Sending /start")

            await conv.send_message("/start")

            # Wait for main menu
            main_menu = await wait_for_buttons(conv)

            if not main_menu:
                print(f"❌ [{account_num}] Main menu not found.")
                return

            # Click Profile
            ok = await click_button_by_text(main_menu, "Профиль")

            if not ok:
                print(f"❌ [{account_num}] Profile button not found.")
                return

            print(f"✅ [{account_num}] Profile clicked")

            # Wait for second menu
            second_menu = await wait_for_buttons(conv)

            if not second_menu:
                print(f"❌ [{account_num}] Second menu not found.")
                return

            # Click Promocode
            ok = await click_button_by_text(second_menu, "Промокод")

            if not ok:
                print(f"❌ [{account_num}] Promocode button not found.")
                return

            print(f"✅ [{account_num}] Promocode clicked")

            # Wait for bot asking code
            try:
                await conv.get_response()
            except:
                pass

            await conv.send_message(spoiler_text)

            print(f"🚀 [{account_num}] Code sent: {spoiler_text}")

    except Exception as e:
        print(f"❌ [{account_num}] {e}")


# ==========================
# ACCOUNT
# ==========================

async def run_account(session_string, account_num):

    client = TelegramClient(
        StringSession(session_string),
        API_ID,
        API_HASH
    )

    try:
        await client.start()

        print(f"✅ Account {account_num} is online")

        channel = await client.get_input_entity(SOURCE_CHANNEL)

    except Exception as e:
        print(f"❌ [{account_num}] Startup Error: {e}")
        return

    @client.on(events.NewMessage(chats=channel))
    async def handler(event):

        spoiler = None

        if event.message.entities:
        text = event.message.message

    print("TEXT:", repr(text))

    for entity in event.message.entities:
        if isinstance(entity, MessageEntitySpoiler):
            print(
                f"SPOILER -> offset={entity.offset}, length={entity.length}"
            )

            spoiler = text[
                entity.offset:
                entity.offset + entity.length
            ]

            print("EXTRACTED:", repr(spoiler))
            break

        if spoiler:
            print(f"📌 [{account_num}] Spoiler detected: {spoiler}")

            asyncio.create_task(
                perform_interaction(
                    client,
                    account_num,
                    spoiler
                )
            )

    await client.run_until_disconnected()


# ==========================
# MAIN
# ==========================

async def main():

    if not SESSION_STRINGS:
        print("No session strings found.")
        return

    await asyncio.gather(*[
        run_account(session, i + 1)
        for i, session in enumerate(SESSION_STRINGS)
    ])


if __name__ == "__main__":
    asyncio.run(main())
