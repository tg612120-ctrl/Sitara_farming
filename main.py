import os
import re
import random
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    FloodWaitError
)

# ==========================================
# CONFIG
# ==========================================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

SESSION_STRINGS = [
    s.strip()
    for s in os.getenv("SESSION_STRINGS", "").split(",")
    if s.strip()
]

SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")
TARGET_BOT = "patrickstarsrobot"

# ==========================================
# GLOBAL STORAGE
# ==========================================

clients = []

conversation_locks = {}

last_redeemed = {}

last_message_ids = {}

processing_promos = {}

# ==========================================
# HELPERS
# ==========================================

async def random_delay():

    await asyncio.sleep(
        random.uniform(0.2, 0.8)
    )


async def wait_for_buttons(
    conv,
    max_messages=10
):

    for _ in range(max_messages):

        msg = await conv.get_response()

        print("\n==========================")
        print(msg.raw_text)

        if msg.buttons:

            print("Buttons:")

            for row in msg.buttons:
                print(
                    [btn.text for btn in row]
                )

            print("==========================\n")

            return msg

    return None


async def click_button(
    message,
    keyword
):

    if not message.buttons:
        return False

    keyword = keyword.lower()

    for row in message.buttons:

        for button in row:

            if keyword in button.text.lower():

                await random_delay()

                await button.click()

                return True

    return False


def extract_promocode(text):

    match = re.search(
        r"[A-Za-z0-9_]{6,}$",
        text
    )

    if match:
        return match.group(0)

    return None


# ==========================================
# MAIN INTERACTION
# ==========================================

async def perform_interaction(
    client,
    account_num,
    promo_code
):

    # Same promo dobara try mat karo
    if last_redeemed.get(account_num) == promo_code:
        print(f"⚠️ [{account_num}] Promo already redeemed.")
        processing_promos[account_num].discard(promo_code)
        return

    lock = conversation_locks[account_num]

    async with lock:

        try:

            # Chhota random delay
            await random_delay()

            async with client.conversation(
                TARGET_BOT,
                timeout=60
            ) as conv:

                print(f"🚀 [{account_num}] Starting redeem")

                await conv.send_message("/start")

                # Main menu
                main_menu = await wait_for_buttons(conv)

                if not main_menu:
                    print(f"❌ [{account_num}] Main menu not received")
                    return

                ok = await click_button(
                    main_menu,
                    "Профиль"
                )

                if not ok:
                    print(f"❌ [{account_num}] Profile button missing")
                    return

                print(f"✅ [{account_num}] Profile clicked")

                # Second menu
                second_menu = await wait_for_buttons(conv)

                if not second_menu:
                    print(f"❌ [{account_num}] Second menu not received")
                    return

                # Click Promocode
                ok = await click_button(
                    second_menu,
                    "Промокод"
                )

                if not ok:
                    print(f"❌ [{account_num}] Promocode button missing")
                    return

                print(f"✅ [{account_num}] Promocode clicked")

                # Wait for bot asking code
                try:
                    await conv.get_response()
                except:
                    pass

                await random_delay()
                await conv.send_message(promo_code)

                last_redeemed[account_num] = promo_code
                print(f"🚀 [{account_num}] Code sent: {promo_code}")

        except FloodWaitError as e:
            print(f"⌛ [{account_num}] FloodWait {e.seconds}s")
            await asyncio.sleep(e.seconds + 1)
        except asyncio.TimeoutError:
            print(f"⌛ [{account_num}] Timeout")
        except Exception as e:
            print(f"❌ [{account_num}] {e}")
        finally:
            processing_promos[account_num].discard(promo_code)


# ==========================================
# ACCOUNT
# ==========================================

async def run_account(session_string, account_num):

    client = TelegramClient(
        StringSession(session_string),
        API_ID,
        API_HASH
    )

    try:

        await client.start()

        me = await client.get_me()

        print(
            f"✅ [{account_num}] "
            f"{me.first_name} "
            f"(@{me.username}) "
            f"connected"
        )

        clients.append(client)

        conversation_locks[
            account_num
        ] = asyncio.Lock()

        last_redeemed[
            account_num
        ] = None

        last_message_ids[
            account_num
        ] = 0

        processing_promos[account_num] = set()

        channel = await client.get_entity(
            SOURCE_CHANNEL
        )

    except Exception as e:

        print(
            f"❌ [{account_num}] Startup Error: {e}"
        )

        return

    while True:
        try:
            messages = await client.get_messages(channel, limit=1)

            if not messages:
                await asyncio.sleep(1)
                continue

            message = messages[0]
            
            # Duplicate message ignore
            if (
                message.id
                <= last_message_ids[
                    account_num
                ]
            ):
                continue

            last_message_ids[
                account_num
            ] = message.id

            text = (
                message.raw_text
                or ""
            )

            promo = extract_promocode(
                text
            )

            if not promo:
                continue
            
            if promo in processing_promos[account_num]:
                continue

            processing_promos[account_num].add(promo)

            print(
                f"📌 [{account_num}] "
                f"Promo detected: {promo}"
            )

            asyncio.create_task(

                perform_interaction(
                    client,
                    account_num,
                    promo
                )

            )
        except Exception as e:

            print(
                f"❌ [{account_num}] "
                f"Polling Error: {e}"
            )
        
        await asyncio.sleep(1)


# ==========================================
# MAIN
# ==========================================

async def main():

    if not SESSION_STRINGS:
        print("❌ No session strings found.")
        return

    print("=" * 50)
    print(f"🚀 Starting {len(SESSION_STRINGS)} accounts...")
    print("=" * 50)

    tasks = []

    for account_num, session in enumerate(
        SESSION_STRINGS,
        start=1
    ):

        tasks.append(

            asyncio.create_task(

                run_account(
                    session,
                    account_num
                )

            )

        )

        # Sab accounts ek hi time connect na kare
        await asyncio.sleep(0.3)

    print("✅ All accounts started.")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
