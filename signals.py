"""
signals.py — MetaPlay by Coinplay
Two broadcasts per day, personalized by user preferences.
  09:00 UTC — morning digest (today's matches filtered by preferences)
  18:00 UTC — evening picks (Mateo's predictions, personalized)
"""
import asyncio, logging, time
from datetime import datetime, timezone
from telegram import Bot
from telegram.constants import ParseMode
from config import State, COINPLAY_URL
from storage import get_all_users, update_user, get_preferences
from messages import MORNING_DIGEST_HEADER, MORNING_DIGEST_FOOTER
from livescore import (
    fetch_match_context,
    format_upcoming_message, format_livescore_message,
)
from predictions import generate_daily_predictions, format_predictions_message
from media import send_pic

logger = logging.getLogger(__name__)

MORNING_HOUR = 9
EVENING_HOUR = 18


def _active_users() -> list[dict]:
    now = time.time()
    return [
        u for u in get_all_users()
        if u.get("state") not in (State.NEW,)
        and now - u.get("last_active", 0) < 7 * 86400
    ]


def _filter_matches_by_prefs(matches: list, prefs: dict) -> list:
    """Filter match list by user sport preference."""
    sport = prefs.get("sport")
    if not sport or sport == "both":
        return matches
    if sport == "football":
        return [m for m in matches if "Football" in m.get("game", "")] or matches
    if sport == "esports":
        return [m for m in matches if "Football" not in m.get("game", "")] or matches
    return matches


async def _send_to(bot: Bot, user_id: int, text: str):
    try:
        await bot.send_message(
            chat_id=user_id, text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        update_user(user_id, last_signal_at=time.time())
    except Exception as e:
        logger.warning(f"Broadcast failed {user_id}: {e}")


async def broadcast_morning_digest(bot: Bot):
    logger.info("Morning digest broadcast...")
    ctx = await fetch_match_context()
    display = ctx["for_display"]
    is_mock = not ctx["has_real"]

    count = 0
    for u in _active_users():
        lang  = u.get("lang", "en")
        prefs = u.get("preferences", {})

        # Personalize match list
        matches = _filter_matches_by_prefs(display["upcoming"], prefs)

        header = MORNING_DIGEST_HEADER.get(lang, MORNING_DIGEST_HEADER["en"])
        body   = format_upcoming_message(matches, lang, is_mock=is_mock)
        footer = MORNING_DIGEST_FOOTER.get(lang, MORNING_DIGEST_FOOTER["en"])

        # Add personalization note
        pref_focus = []
        if prefs.get("leagues"):
            pref_focus.extend(prefs["leagues"][:2])
        if pref_focus:
            focus_str = ", ".join(pref_focus)
            note = f"\n_Showing matches for: {focus_str}_" if lang == "en" else f"\n_Mostrando partidos de: {focus_str}_"
            body += note

        full_text = header + body + footer
        img_sent = await send_pic(bot, u["user_id"], "morning", full_text, lang)
        if not img_sent:
            await _send_to(bot, u["user_id"], full_text)
        count += 1
        await asyncio.sleep(0.05)

    logger.info(f"Morning digest: {count} users")


async def broadcast_daily_signal(bot: Bot):
    logger.info("Evening picks broadcast...")
    ctx = await fetch_match_context()
    is_mock = not ctx["has_real"]

    count = 0
    for u in _active_users():
        lang  = u.get("lang", "en")
        state = u.get("state", State.WARMUP)
        prefs = u.get("preferences", {})

        # Personalize: use real matches filtered by prefs
        ai_matches = _filter_matches_by_prefs(ctx["live"] + ctx["upcoming"], prefs) if ctx["has_real"] else []
        picks = await generate_daily_predictions(ai_matches, lang)
        text  = format_predictions_message(picks, lang)

        # Add Coinplay CTA for converting/repeat users
        if state in (State.CONVERTING, State.REPEAT, State.DEPOSITED):
            text += f"\n\n👉 {COINPLAY_URL}"

        img_sent = await send_pic(bot, u["user_id"], "picks", text, lang)
        if not img_sent:
            await _send_to(bot, u["user_id"], text)
        count += 1
        await asyncio.sleep(0.08)

    logger.info(f"Evening picks: {count} users")


async def run_signal_scheduler(bot: Bot):
    while True:
        now = datetime.now(timezone.utc)
        schedules = [MORNING_HOUR, EVENING_HOUR]
        secs_opts = []
        for h in schedules:
            diff = ((h - now.hour) % 24) * 3600 - now.minute * 60 - now.second
            if diff <= 0:
                diff += 86400
            secs_opts.append((diff, h))

        next_secs, next_hour = min(secs_opts)
        logger.info(f"Next broadcast {next_hour:02d}:00 UTC in {next_secs/3600:.1f}h")
        await asyncio.sleep(next_secs)

        if next_hour == MORNING_HOUR:
            await broadcast_morning_digest(bot)
        else:
            await broadcast_daily_signal(bot)
