"""
ftd_onboarding.py — MetaPlay by Coinplay
Post-FTD repeat deposit push machine.
Schedule: r1h → r6h → r24h → r3d → r7d
"""
import asyncio, logging, time
from telegram import Bot
from telegram.constants import ParseMode
from config import REPEAT_SCHEDULE, REPEAT_ENABLED, State, COINPLAY_URL
from storage import get_all_users, get_user, update_user
from messages import REPEAT_PUSH
from media import send_pic, get_repeat_moment

logger = logging.getLogger(__name__)

async def start_repeat_machine(bot: Bot, user_id: int, chat_id: int, lang: str):
    """Launch repeat FTD push sequence after first deposit confirmed."""
    if not REPEAT_ENABLED:
        # channel-режим: повторные дожимы выключены для этого бренда
        return
    u = get_user(user_id)
    update_user(user_id, state=State.REPEAT, repeat_idx=0, repeat_sent_at=time.time())
    asyncio.create_task(_repeat_loop(bot, user_id, chat_id, lang))

async def _repeat_loop(bot: Bot, user_id: int, chat_id: int, lang: str, start_idx: int = 0):
    pushes = REPEAT_PUSH.get(lang, REPEAT_PUSH["en"])

    for idx, delay in enumerate(REPEAT_SCHEDULE):
        if idx < start_idx:
            continue
        await asyncio.sleep(delay)

        # Re-check user state — if they're gone or manually stopped, skip
        u = get_user(user_id)
        if u.get("repeat_idx", 0) > idx:
            continue  # already sent by another task somehow

        if idx >= len(pushes):
            break

        text = pushes[idx]
        # Append Coinplay link to r24h and beyond
        if idx >= 2:
            text += f"\n\n👉 {COINPLAY_URL}"

        try:
            lang_u = get_user(user_id).get("lang", "en")
            moment = get_repeat_moment(idx)
            sent = await send_pic(bot, chat_id, moment, text, lang_u)
            if not sent:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
            update_user(user_id, repeat_idx=idx + 1, repeat_sent_at=time.time())
            logger.info(f"Repeat push r{idx} sent to {user_id} (image: {moment})")
        except Exception as e:
            logger.error(f"Repeat push error for {user_id}: {e}")
            break


async def resume_pending_repeats(bot: Bot):
    """
    On bot restart — resume any in-flight repeat sequences.
    Calculates remaining delay based on repeat_sent_at.
    """
    now = time.time()
    for u in get_all_users():
        if u.get("state") != State.REPEAT:
            continue

        user_id    = u["user_id"]
        chat_id    = user_id  # 1:1 private chat
        lang       = u.get("lang", "en")
        repeat_idx = u.get("repeat_idx", 0)
        sent_at    = u.get("repeat_sent_at") or u.get("ftd_at") or now

        if repeat_idx >= len(REPEAT_SCHEDULE):
            continue

        # Figure out how much time is left for the next push
        elapsed  = now - sent_at
        delay    = REPEAT_SCHEDULE[repeat_idx]
        remaining = max(0, delay - elapsed)

        logger.info(f"Resuming repeat for {user_id}: idx={repeat_idx}, remaining={remaining:.0f}s")

        async def _launch(uid=user_id, cid=chat_id, l=lang, start=repeat_idx, rem=remaining):
            await asyncio.sleep(rem)
            await _repeat_loop(bot, uid, cid, l, start_idx=start)

        asyncio.create_task(_launch())
