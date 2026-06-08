"""
media.py — MetaPlay by Coinplay
Centralized image management. Maps each funnel moment to its branded image.

Images live in pics/ folder (relative to bot.py).
Each image is cached as Telegram file_id after first send to avoid re-uploading.

Moment → Image mapping:
  start       → 19.png   "Focus Win Repeat" — cinematic city
  onboarding1 → 110.png  Demon at keyboard — intense
  onboarding2 → 111.png  Demon flying forward — momentum
  bridge      → 113.png  Demon celebrating at PC — "I'm winning"
  cta         → 114.png  Demon plotting — focused
  ftd         → 112.png  VICTORY + trophy
  morning     → 115.png  GAME ON
  picks       → 114.png  Demon plotting
  repeat_1    → 116.png  Demon raging — urgency
  repeat_2    → 117.png  Crystal trophy — reward
"""
import os
import logging
import random
import re
from telegram import Bot, InlineKeyboardMarkup
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

PICS_DIR = os.path.join(os.path.dirname(__file__), "pics")

# ── Moment → filename mapping (берётся из активного бренда) ───────────────────
from brand import BRAND
MOMENT_PICS = dict(BRAND.images)

# Repeat push index → moment
REPEAT_MOMENT = {
    0: "repeat_hot",   # r1h — urgent
    1: "repeat_hot",   # r6h — urgent
    2: "repeat_win",   # r24h — reward
    3: "repeat_win",   # r3d — reward
    4: "repeat_win",   # r7d — reward
}

# ── File ID cache (avoids re-uploading same image) ───────────────────────────
# Populated on first send, reused after
_file_id_cache: dict[str, str] = {}


def sanitize_markdown(text: str) -> str:
    """
    Sanitize text so Telegram's MarkdownV1 parser won't choke on it.

    Rules for Telegram Markdown (legacy/V1):
      *bold*   — must be paired
      _italic_ — must be paired
      `code`   — must be paired
      [text](url) — inline links

    Strategy: balance unpaired * and _ markers, escape literal backticks
    that aren't code fences, and leave everything else intact.
    """
    if not text:
        return text

    # Fix unpaired * (bold markers)
    # Count occurrences — if odd, remove the last lone one
    parts = text.split("*")
    if len(parts) % 2 == 0:
        # Odd number of * — join with escaped version for the trailing one
        text = "*".join(parts[:-1]) + parts[-1]
    # Re-check: just ensure count is even by stripping trailing lone *
    if text.count("*") % 2 != 0:
        # Find and remove the last * that has no pair
        idx = text.rfind("*")
        text = text[:idx] + text[idx+1:]

    # Fix unpaired _ (italic markers)
    # Be careful: don't touch _ inside URLs or words like "begin_at"
    # Only treat _ as italic when surrounded by spaces or at start/end
    italic_count = len(re.findall(r'(?<!\w)_(?!\w)|(?<=\w)_(?=\s)|(?<=\s)_(?=\w)', text))
    if italic_count % 2 != 0:
        # Find last formatting _ and remove it
        for match in reversed(list(re.finditer(r'(?<!\w)_|_(?!\w)', text))):
            text = text[:match.start()] + text[match.end():]
            break

    # Fix unpaired backticks
    if text.count("`") % 2 != 0:
        idx = text.rfind("`")
        text = text[:idx] + text[idx+1:]

    return text


def _pic_path(filename: str) -> str:
    return os.path.join(PICS_DIR, filename)


def _pic_exists(filename: str) -> bool:
    return os.path.exists(_pic_path(filename))


# ── Core send function ────────────────────────────────────────────────────────

async def send_pic(
    bot: Bot,
    chat_id: int,
    moment: str,
    caption: str,
    lang: str = "en",
    reply_markup=None,
    parse_mode: str = ParseMode.MARKDOWN,
) -> bool:
    """
    Send branded image for a funnel moment with caption.
    Falls back to text-only if image not found.
    Returns True if image sent, False if fell back to text.
    """
    filename = MOMENT_PICS.get(moment)
    if not filename or not _pic_exists(filename):
        logger.warning(f"Image not found for moment '{moment}': {filename}")
        # Fallback: send text only
        await bot.send_message(
            chat_id=chat_id,
            text=sanitize_markdown(caption),
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
        return False

    # Try file_id cache first (faster, no re-upload)
    file_id = _file_id_cache.get(filename)
    safe_caption = sanitize_markdown(caption)

    try:
        if file_id:
            msg = await bot.send_photo(
                chat_id=chat_id,
                photo=file_id,
                caption=safe_caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        else:
            with open(_pic_path(filename), "rb") as f:
                msg = await bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=safe_caption,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
            # Cache the file_id for future sends
            if msg.photo:
                _file_id_cache[filename] = msg.photo[-1].file_id
                logger.info(f"Cached file_id for {filename}")

        return True

    except Exception as e:
        logger.error(f"send_pic failed for {filename}: {e}")
        # Fallback to text
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=safe_caption,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
        except Exception as e2:
            logger.error(f"Text fallback also failed: {e2}")
        return False


async def send_random_pic(
    bot: Bot,
    chat_id: int,
    caption: str,
    exclude: list[str] = None,
    reply_markup=None,
) -> bool:
    """Send a random branded image — for variety in repeat pushes."""
    available = [f for f in MOMENT_PICS.values() if f not in (exclude or [])]
    if not available:
        return False
    filename = random.choice(available)
    moment   = next(k for k, v in MOMENT_PICS.items() if v == filename)
    return await send_pic(bot, chat_id, moment, caption, reply_markup=reply_markup)


def get_repeat_moment(repeat_idx: int) -> str:
    """Get image moment for repeat push index."""
    return REPEAT_MOMENT.get(repeat_idx, "repeat_hot")


def pics_available() -> dict[str, bool]:
    """Check which images are available — for /apitest."""
    return {moment: _pic_exists(fname) for moment, fname in MOMENT_PICS.items()}
