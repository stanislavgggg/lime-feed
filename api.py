"""
api.py — MetaPlay HTTP API for the Mini App

Fully async — runs on asyncio, no threading issues.
Uses only stdlib (no aiohttp dependency needed).

Endpoints:
  GET  /api/health
  GET  /api/config                       — режим воронки (product/channel) + куда вести CTA.
                                           Делает фронт зеркалом бэка: один источник правды.
  GET  /api/live
  GET  /api/upcoming
  GET  /api/news?category=all|crypto|casino|esports[&limit=40]
                                           — авто-лента: бесплатные RSS/JSON (крипто/казино/киберспорт)
                                           + крипто-рынок (CoinGecko, Fear&Greed). Без гейтинга.
  GET  /api/picks?lang=en[&uid=123]     — uid → гейтинг пиков для неподписчиков
  GET  /api/stats
  GET  /api/membership?uid=123          — рычаг №1: проверка подписки на канал
  POST /api/event   {event, uid?, meta?} — рычаг №5: событийная аналитика воронки
  GET  /api/funnel                       — счётчики воронки + конверсии (для CRO)
"""
import asyncio
import json
import logging
import os
from urllib.parse import urlparse, parse_qs

from predictions import generate_daily_predictions, apply_gate, _preds
from livescore import fetch_match_context, get_live_esports, get_live_football, get_upcoming_esports, get_today_football
from news import get_news, VALID_CATEGORIES
from config import HONEST_STATS, CTA_GATE, CHANNEL_HANDLE, CHANNEL_URL
from brand import BRAND, CTAMode
import membership
import analytics

logger = logging.getLogger(__name__)
PORT        = int(os.environ.get("PORT", os.environ.get("API_PORT", 8080)))
CORS_ORIGIN = os.environ.get("MINI_APP_ORIGIN", "*")


def _stats_payload() -> dict:
    """Единый, ЧЕСТНЫЙ источник статистики для /api/stats и /api/picks.

    HONEST_STATS=True (канал): пока picks<5 — rate=None и note='accumulating',
    никаких дутых процентов. Доверие = валюта конверсии даже в бесплатный канал.
    """
    stats   = _preds.get("stats", {"correct": 0, "total": 0})
    total   = stats["total"]
    correct = stats["correct"]
    if total >= 5:
        rate = round(correct / total * 100)
    elif HONEST_STATS:
        rate = None
    else:
        rate = round(correct / total * 100) if total > 0 else None
    return {
        "correct": correct,
        "total":   total,
        "rate":    rate,
        "note":    "accumulating" if total < 5 else "real",
    }


def _json_bytes(data) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def _cors_headers(body: bytes) -> list[tuple[str, str]]:
    return [
        ("Content-Type",                 "application/json; charset=utf-8"),
        ("Access-Control-Allow-Origin",  CORS_ORIGIN),
        ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
        ("Access-Control-Allow-Headers", "Content-Type"),
        ("Content-Length",               str(len(body))),
    ]


# ── Route handlers (all async) ────────────────────────────────────────────────

async def handle_health() -> tuple[int, bytes]:
    return 200, _json_bytes({"status": "ok"})


async def handle_config() -> tuple[int, bytes]:
    """
    Публичная идентичность бренда + РЕЖИМ воронки. Это «единый мозг» для фронта:
    мини-апп рендерит product-оффер ИЛИ канальную подписку строго по mode отсюда,
    ничего не хардкодя. Куда вести CTA — тоже берётся отсюда (cta.url / bot_username),
    поэтому фронт и бэк физически не могут разъехаться по продукту/каналу.
    Секреты не отдаём — только несекретная идентичность.
    """
    b = BRAND
    is_channel = b.cta.mode is CTAMode.CHANNEL

    offer = None
    if not is_channel:
        o = b.offer
        offer = {
            "bonus_pct":    o.bonus_pct,
            "bonus_max":    o.bonus_max,
            "free_spins":   o.free_spins,
            "min_deposit":  o.min_deposit,
            "wagering":     o.wagering,
            "cashback_pct": o.cashback_pct,
            "currencies":   o.currencies,
            "currency":     o.currency,
        }

    we, wf = b.sport.wants_esports(), b.sport.wants_football()
    if we and wf:
        markets = {"en": "Football & Esports", "es": "Fútbol y Esports"}
    elif wf:
        markets = {"en": "Football", "es": "Fútbol"}
    else:
        markets = {"en": "Esports", "es": "Esports"}

    return 200, _json_bytes({
        "brand":        b.id,
        "display_name": b.display_name,
        "tagline":      b.tagline,                       # {en, es}
        "character":    {"name": b.character.name, "role": b.character.role},
        "mode":         b.cta.mode.value,                # "product" | "channel"
        "show_offer":   not is_channel,                  # фронт прячет оффер в channel-режиме
        "cta": {
            "label":        b.cta.button_label,          # {en, es}
            "url":          b.cta.primary_url(),         # channel_url (channel) | reg_url (product)
            "channel":      b.cta.channel_handle or "",
            "channel_url":  b.cta.channel_url or "",
            "gate":         bool(b.cta.gate),
            "bot_username": b.bot_username,              # для deep link t.me/<bot>?start=join
            "partner_name": b.cta.partner_name or "",
        },
        "offer":            offer,                       # null в channel-режиме
        "markets":          markets,
        "honest_stats":     b.character.honest_stats,
        "win_rate_display": b.character.win_rate_display,
        "privacy_url":      b.privacy_url,
    })


async def handle_stats() -> tuple[int, bytes]:
    return 200, _json_bytes(_stats_payload())


async def handle_live() -> tuple[int, bytes]:
    (live_e, _), (live_f, _) = await asyncio.gather(
        get_live_esports(),
        get_live_football(),
    )
    return 200, _json_bytes({"matches": live_e + live_f})


async def handle_upcoming() -> tuple[int, bytes]:
    (up_e, _), (today_f, _) = await asyncio.gather(
        get_upcoming_esports(24),
        get_today_football(),
    )
    return 200, _json_bytes({"matches": up_e + today_f})


async def handle_news(category: str, limit: int) -> tuple[int, bytes]:
    """Live content feed (crypto / casino / esports) for the Mini App 'Feed' surface.

    Free public feeds only, aggregated + cached in news.py. Never gated — this is
    top-of-funnel content that keeps the app worth opening between match days.
    """
    data = await get_news(category=category, limit=limit)
    return 200, _json_bytes(data)


async def handle_picks(lang: str, uid: int | None) -> tuple[int, bytes]:
    ctx          = await fetch_match_context()
    real_matches = ctx.get("upcoming", [])
    picks        = await generate_daily_predictions(real_matches, lang)

    # Гейтинг (рычаг №3): неподписчику отдаём первый пик целиком + тизеры остальных.
    gated  = False
    member = True
    if CTA_GATE and membership.channel_configured():
        member = await membership.is_member(uid) if uid else False
        picks  = apply_gate(picks, member=member, free_count=1)
        gated  = not member
        analytics.track("membership_check", uid)
        if uid and member:
            analytics.mark_join(uid)

    return 200, _json_bytes({
        "picks":  picks,
        "stats":  _stats_payload(),
        "source": "real" if real_matches else "no_matches",
        "gate":   {
            "enabled":     bool(CTA_GATE and membership.channel_configured()),
            "locked":      gated,           # True → есть скрытые за подпиской пики
            "is_member":   member,
            "channel":     CHANNEL_HANDLE or CHANNEL_URL,
        },
    })


async def handle_membership(uid: int | None) -> tuple[int, bytes]:
    """Рычаг №1: подписка как ключ. Мини-апп бьёт сюда и мгновенно разблокирует контент."""
    if not uid:
        return 400, _json_bytes({"error": "uid_required"})
    analytics.track("membership_check", uid)
    member = await membership.is_member(uid)
    if member:
        analytics.mark_join(uid)
    enabled = bool(CTA_GATE and membership.channel_configured())
    return 200, _json_bytes({
        "uid":       uid,
        "member":    member,
        "gate": {
            "enabled":   enabled,
            "locked":    enabled and not member,
            "is_member": member,
            "channel":   CHANNEL_HANDLE or CHANNEL_URL,
        },
        "channel":   CHANNEL_HANDLE or CHANNEL_URL,
        "configured": membership.channel_configured(),
    })


async def handle_event(body: dict) -> tuple[int, bytes]:
    """Рычаг №5: фронт шлёт события воронки (cta_view/cta_tap/channel_open/…)."""
    event = (body or {}).get("event")
    if not event or not isinstance(event, str):
        return 400, _json_bytes({"error": "event_required"})
    uid  = body.get("uid")
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else None
    analytics.track(event, uid if isinstance(uid, int) else None, meta)
    return 200, _json_bytes({"ok": True, "event": event})


async def handle_funnel() -> tuple[int, bytes]:
    """Счётчики воронки + конверсии — основа CRO (мерим до того, как крутить тексты)."""
    return 200, _json_bytes(analytics.snapshot())


# ── Async HTTP server ─────────────────────────────────────────────────────────

async def handle_request(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        # Read headers (until blank line), then body per Content-Length.
        raw = b""
        while b"\r\n\r\n" not in raw:
            chunk = await reader.read(4096)
            if not chunk:
                break
            raw += chunk
            if len(raw) > 1_048_576:  # 1 MB guard
                break
        if not raw:
            writer.close()
            return

        head, _, rest = raw.partition(b"\r\n\r\n")
        header_text = head.decode("utf-8", errors="replace")
        lines       = header_text.split("\r\n")
        first_line  = lines[0] if lines else ""
        parts       = first_line.split(" ")
        method      = parts[0] if parts else "GET"
        full_path   = parts[1] if len(parts) > 1 else "/"

        # Content-Length → дочитываем тело (для POST)
        content_length = 0
        for ln in lines[1:]:
            if ln.lower().startswith("content-length:"):
                try:
                    content_length = int(ln.split(":", 1)[1].strip())
                except ValueError:
                    content_length = 0
                break
        body_bytes = rest
        while len(body_bytes) < content_length:
            chunk = await reader.read(content_length - len(body_bytes))
            if not chunk:
                break
            body_bytes += chunk

        parsed = urlparse(full_path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)

        def _uid() -> int | None:
            try:
                return int(qs.get("uid", [""])[0])
            except (ValueError, TypeError):
                return None

        # OPTIONS preflight
        if method == "OPTIONS":
            response = (
                b"HTTP/1.1 204 No Content\r\n"
                b"Access-Control-Allow-Origin: *\r\n"
                b"Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
                b"Access-Control-Allow-Headers: Content-Type\r\n"
                b"Content-Length: 0\r\n\r\n"
            )
            writer.write(response)
            await writer.drain()
            writer.close()
            return

        # Route
        try:
            if path == "/api/health":
                status, body = await handle_health()
            elif path == "/api/config":
                status, body = await handle_config()
            elif path == "/api/stats":
                status, body = await handle_stats()
            elif path == "/api/live":
                status, body = await handle_live()
            elif path == "/api/upcoming":
                status, body = await handle_upcoming()
            elif path == "/api/news":
                cat = (qs.get("category", ["all"])[0] or "all").lower()
                if cat not in VALID_CATEGORIES:
                    cat = "all"
                try:
                    lim = int(qs.get("limit", ["40"])[0])
                except (ValueError, TypeError):
                    lim = 40
                lim = max(1, min(lim, 60))
                status, body = await handle_news(cat, lim)
            elif path == "/api/picks":
                lang = (qs.get("lang", ["en"])[0] or "en").lower()
                if lang not in ("en", "ru", "es"):
                    lang = "en"
                status, body = await handle_picks(lang, _uid())
            elif path == "/api/membership":
                status, body = await handle_membership(_uid())
            elif path == "/api/funnel":
                status, body = await handle_funnel()
            elif path == "/api/event" and method == "POST":
                try:
                    payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
                except (json.JSONDecodeError, UnicodeDecodeError):
                    payload = {}
                status, body = await handle_event(payload)
            else:
                status, body = 404, _json_bytes({"error": "not_found"})
        except Exception as e:
            logger.error(f"{path} handler error: {e}", exc_info=True)
            status, body = 500, _json_bytes({"error": "internal_error"})

        headers = _cors_headers(body)
        status_text = {200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Internal Server Error"}.get(status, "OK")
        header_lines = "\r\n".join(f"{k}: {v}" for k, v in headers)
        response_head = f"HTTP/1.1 {status} {status_text}\r\n{header_lines}\r\n\r\n".encode()

        writer.write(response_head + body)
        await writer.drain()
        logger.info(f'"{method} {path} HTTP/1.1" {status} -')

    except Exception as e:
        logger.error(f"Request handling error: {e}")
    finally:
        writer.close()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    server = await asyncio.start_server(handle_request, "0.0.0.0", PORT)
    logger.info(f"MetaPlay Mini App API listening on :{PORT}")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
