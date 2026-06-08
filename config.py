"""
config.py — тонкий шим совместимости
=====================================

Раньше тут лежало всё вперемешку. Теперь:
    • СЕКРЕТЫ (токены, ключи API) — читаются из окружения здесь.
    • БРЕНД (оффер, ссылки, персонаж, вид спорта, язык) — берётся из brand.BRAND.

Имена сохранены 1:1 со старой версией, поэтому остальной код не трогаем:
`from config import OFFER, COINPLAY_REG_URL, ESPORTS_GAMES, ...` продолжает работать.
"""
import os

from brand import BRAND, CTAMode  # noqa: F401  (CTAMode может пригодиться импортёрам)

# ── Секреты (только окружение, в код не попадают) ─────────────────────────────
BOT_TOKEN      = os.environ["BOT_TOKEN"]
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
PANDASCORE_KEY = os.environ.get("PANDASCORE_KEY", "")
RAPIDAPI_KEY   = os.environ.get("RAPIDAPI_KEY", "")

# ── Идентичность бренда ───────────────────────────────────────────────────────
BOT_USERNAME = BRAND.bot_username
BRAND_NAME   = BRAND.display_name

# ── Внешние API ───────────────────────────────────────────────────────────────
FOOTBALL_API_HOST = "free-api-live-football-data.p.rapidapi.com"

# ── Настройки ИИ ──────────────────────────────────────────────────────────────
AI_MODEL      = "claude-sonnet-4-20250514"
AI_MAX_TOKENS = 300

# ── Ссылки CTA (режим product/channel прозрачно учтён) ────────────────────────
CTA_MODE         = BRAND.cta.mode                 # CTAMode.PRODUCT | CTAMode.CHANNEL
COINPLAY_URL     = BRAND.cta.click_url
COINPLAY_REG_URL = BRAND.cta.primary_url()        # в channel-режиме = ссылка на канал
CHANNEL_URL      = BRAND.cta.channel_url
CHANNEL_HANDLE   = BRAND.cta.channel_handle
CHANNEL_CHAT_REF = BRAND.cta.channel_chat_ref()   # для getChatMember ('@handle' / '-100…')
CTA_GATE         = BRAND.cta.gate                 # гейтить контент за подпиской на канал
PARTNER_NAME     = BRAND.cta.partner_name

# ── Доверие / честность статистики ────────────────────────────────────────────
HONEST_STATS     = BRAND.character.honest_stats   # True → только реальные накопленные цифры

# ── Оффер ─────────────────────────────────────────────────────────────────────
OFFER = {
    "bonus_pct":    BRAND.offer.bonus_pct,
    "bonus_max":    BRAND.offer.bonus_max,
    "free_spins":   BRAND.offer.free_spins,
    "min_deposit":  BRAND.offer.min_deposit,
    "wagering":     BRAND.offer.wagering,
    "cashback_pct": BRAND.offer.cashback_pct,
    "currencies":   BRAND.offer.currencies,
}

# ── Вид спорта / данные ───────────────────────────────────────────────────────
ESPORTS_GAMES    = list(BRAND.sport.esports_games)
GAME_DISPLAY     = dict(BRAND.sport.game_display)
FOOTBALL_LEAGUES = dict(BRAND.sport.football_leagues)
VERTICAL         = BRAND.sport.vertical
WANTS_ESPORTS    = BRAND.sport.wants_esports()
WANTS_FOOTBALL   = BRAND.sport.wants_football()

# ── Предсказания / воронка ────────────────────────────────────────────────────
MATEO_WIN_RATE   = BRAND.character.win_rate_display
MAX_DAILY_PICKS  = BRAND.funnel.max_daily_picks
ONBOARDING_TURNS = BRAND.funnel.onboarding_turns
REPEAT_ENABLED   = BRAND.funnel.repeat_enabled
REPEAT_SCHEDULE  = list(BRAND.funnel.repeat_schedule)

# ── Языки / гео ───────────────────────────────────────────────────────────────
SUPPORTED_LANGS = set(BRAND.i18n.supported)
DEFAULT_LANG    = BRAND.i18n.default
GEO_LANG        = dict(BRAND.i18n.geo_lang)
TG_LANG_MAP     = dict(BRAND.i18n.tg_lang_map)


# ── Состояния воронки ─────────────────────────────────────────────────────────
class State:
    NEW        = "new"
    WARMUP     = "warmup"
    BRIDGE     = "bridge"
    CONVERTING = "converting"
    DEPOSITED  = "deposited"
    REPEAT     = "repeat"


# ── Хранилище / картинки ──────────────────────────────────────────────────────
DB_PATH    = os.environ.get("DB_PATH", "users.json")
HOOK_IMAGE = os.environ.get("HOOK_IMAGE", "hook.png")
