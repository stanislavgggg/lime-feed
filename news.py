"""
news.py — MetaPlay live content feed for the Mini App.

Aggregates FREE, no-key public feeds into a single normalized list so the
Mini App can fill its "Feed" surface with auto-updating crypto / casino /
esports content. No API keys here on purpose — nothing to leak, nothing to
rate-limit into the ground.

Sources (all free, no auth):
  Crypto   RSS  — CoinDesk, Cointelegraph, Decrypt
  Casino   RSS  — GamblingNews.com, Casino.org
  Esports  JSON — VLR.gg results mirror (vlr.orlandomm.net)
  Market   JSON — CoinGecko /global  +  alternative.me Fear & Greed

Public surface:
  await get_news(category="all", limit=40)  -> {"items":[...], "market":{...}, "updated_at": iso}

Everything is cached in-memory with a TTL and fails soft: a dead feed is
skipped, never fatal.
"""
from __future__ import annotations

import asyncio
import html
import logging
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
NEWS_TTL   = 600   # 10 min — news doesn't move that fast
MARKET_TTL = 180   # 3 min  — prices do
HTTP_TIMEOUT = 12.0
MAX_PER_FEED = 12  # cap per source so one chatty feed can't dominate

# category -> list of (source_label, url)
# Niche feeds give nice images/sources when they load; Google News RSS is a
# reliability backstop — its servers almost never block server-side fetches,
# so the feed is never empty even when a CDN-protected outlet 403s us.
def _gnews(query: str) -> str:
    from urllib.parse import quote
    return f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"


RSS_FEEDS: dict[str, list[tuple[str, str]]] = {
    "crypto": [
        ("CoinDesk",      "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("Decrypt",       "https://decrypt.co/feed"),
    ],
    "casino": [
        ("GamblingNews",  "https://www.gamblingnews.com/feed/"),
        ("Casino.org",    "https://www.casino.org/news/feed/"),
    ],
    # Esports needs a real news source: VLR (below) only gives match scores and
    # was the thing crashing All/Esports. Google News RSS is the reliable feed;
    # HLTV is a bonus that may or may not pass a datacenter Cloudflare check.
    "esports": [
        ("HLTV",        "https://www.hltv.org/rss/news"),
        ("Google News", _gnews("esports OR CS2 OR Valorant OR Dota2 when:3d")),
    ],
}

VLR_RESULTS_URL = "https://vlr.orlandomm.net/api/v1/results"
CG_GLOBAL_URL   = "https://api.coingecko.com/api/v3/global"
CG_MARKETS_URL  = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&ids=bitcoin,ethereum,solana&sparkline=false"
)
FNG_URL         = "https://api.alternative.me/fng/?limit=1"

# A real browser UA — many news CDNs (Cloudflare) reject non-browser agents,
# which is why API services (CoinGecko, Fear&Greed) work but RSS came back empty.
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
_RSS_ACCEPT = "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5"

# ── Cache ───────────────────────────────────────────────────────────────────--
_cache: dict[str, dict] = {}


def _cached(key: str):
    e = _cache.get(key)
    if e and time.time() - e["ts"] < e["ttl"]:
        return e["data"]
    return None


def _set_cache(key: str, data, ttl: int):
    _cache[key] = {"ts": time.time(), "data": data, "ttl": ttl}


# ── Helpers ────────────────────────────────────────────────────────────────---
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE  = re.compile(r"\s+")
_IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)


def _strip_html(s: str | None, limit: int = 220) -> str:
    if not s:
        return ""
    s = _TAG_RE.sub(" ", s)
    s = html.unescape(s)
    s = _WS_RE.sub(" ", s).strip()
    return (s[: limit - 1] + "…") if len(s) > limit else s


def _to_iso(date_str: str | None) -> str:
    """pubDate (RFC-822, RSS) or updated/published (ISO-8601, Atom) → ISO-8601 UTC.

    Falls back to 'now' on garbage so the item still sorts sanely.
    """
    if date_str:
        s = date_str.strip()
        # ISO-8601 (Atom): 2025-06-04T10:00:00Z / +00:00
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
        # RFC-822 (RSS): Wed, 04 Jun 2025 14:30:00 GMT
        try:
            dt = parsedate_to_datetime(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, IndexError):
            pass
    return datetime.now(timezone.utc).isoformat()


def _first_image(item: ET.Element, description: str) -> str | None:
    # 1) <media:content url> / <media:thumbnail url>
    for tag in ("{http://search.yahoo.com/mrss/}content",
                "{http://search.yahoo.com/mrss/}thumbnail"):
        el = item.find(tag)
        if el is not None and el.get("url"):
            return el.get("url")
    # 2) <enclosure url type="image/...">
    enc = item.find("enclosure")
    if enc is not None and (enc.get("type") or "").startswith("image") and enc.get("url"):
        return enc.get("url")
    # 3) first <img> inside the description / content:encoded
    m = _IMG_RE.search(description or "")
    if m:
        return m.group(1)
    return None


def _stable_id(url: str) -> str:
    return str(abs(hash(url)) % (10 ** 12))


def _parse_rss(xml_text: str, source: str, category: str) -> list[dict]:
    """Parse an RSS/Atom string into normalized news items. Never raises."""
    items: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("RSS parse error (%s): %s", source, e)
        return items

    # RSS 2.0: channel/item   |   Atom: feed/entry
    nodes = root.findall(".//item")
    is_atom = False
    if not nodes:
        nodes = root.findall("{http://www.w3.org/2005/Atom}entry")
        is_atom = True

    for n in nodes[:MAX_PER_FEED]:
        if is_atom:
            title = (n.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            link_el = n.find("{http://www.w3.org/2005/Atom}link")
            link = (link_el.get("href") if link_el is not None else "") or ""
            desc = (n.findtext("{http://www.w3.org/2005/Atom}summary")
                    or n.findtext("{http://www.w3.org/2005/Atom}content") or "")
            pub = (n.findtext("{http://www.w3.org/2005/Atom}updated")
                   or n.findtext("{http://www.w3.org/2005/Atom}published"))
        else:
            title = (n.findtext("title") or "").strip()
            link = (n.findtext("link") or "").strip()
            desc = (n.findtext("{http://purl.org/rss/1.0/modules/content/}encoded")
                    or n.findtext("description") or "")
            pub = n.findtext("pubDate")

        if not title or not link:
            continue

        items.append({
            "id":           _stable_id(link),
            "title":        html.unescape(title),
            "url":          link,
            "source":       source,
            "category":     category,
            "published_at": _to_iso(pub if not is_atom else pub),
            "image":        _first_image(n, desc),
            "summary":      _strip_html(desc),
        })
    return items


# ── Fetchers ───────────────────────────────────────────────────────────────---

async def _fetch_text(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        r = await client.get(url, headers={"User-Agent": _UA, "Accept": _RSS_ACCEPT})
        r.raise_for_status()
        return r.text
    except Exception as e:  # noqa: BLE001 — feeds fail soft
        logger.warning("feed fetch failed %s: %s", url, type(e).__name__)
        return None


async def _fetch_json(client: httpx.AsyncClient, url: str):
    try:
        r = await client.get(url, headers={"User-Agent": _UA, "Accept": "application/json"})
        r.raise_for_status()
        return r.json()
    except Exception as e:  # noqa: BLE001
        logger.warning("json fetch failed %s: %s", url, type(e).__name__)
        return None


async def _fetch_rss_category(client, category: str) -> list[dict]:
    feeds = RSS_FEEDS.get(category, [])
    texts = await asyncio.gather(*[_fetch_text(client, u) for _, u in feeds])
    out: list[dict] = []
    for (source, _), text in zip(feeds, texts):
        if text:
            out.extend(_parse_rss(text, source, category))
    return out


async def _fetch_esports(client) -> list[dict]:
    """VLR.gg match results → news items. Bulletproof: any failure → []."""
    out: list[dict] = []
    try:
        data = await _fetch_json(client, VLR_RESULTS_URL)
        if not data:
            return out
        # The API has shipped two shapes over time:
        #   {"data": {"segments": [...]}}   and   {"data": [...]}
        d = data.get("data") if isinstance(data, dict) else data
        if isinstance(d, dict):
            results = d.get("segments") or d.get("results") or []
        elif isinstance(d, list):
            results = d
        else:
            results = []
        for r in (results or [])[:MAX_PER_FEED]:
            if not isinstance(r, dict):
                continue
            try:
                t1, t2 = r.get("team1", "?"), r.get("team2", "?")
                s1, s2 = r.get("score1", ""), r.get("score2", "")
                event  = (r.get("tournament_name") or r.get("tournament")
                          or r.get("event") or "Esports")
                title  = f"{t1} {s1}–{s2} {t2}".strip()
                mp     = r.get("match_page", "") or ""
                link   = mp if mp.startswith("http") else ("https://www.vlr.gg" + mp)
                out.append({
                    "id":           _stable_id(link + title),
                    "title":        title,
                    "url":          link,
                    "source":       "VLR.gg",
                    "category":     "esports",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "image":        None,
                    "summary":      f"{event} · {r.get('round_info', 'Result')}",
                })
            except Exception:  # noqa: BLE001 — skip a bad row, keep the rest
                continue
    except Exception as e:  # noqa: BLE001 — VLR must never break the feed
        logger.warning("esports fetch failed: %s", type(e).__name__)
    return out


async def _fetch_market(client) -> dict:
    cached = _cached("market")
    if cached is not None:
        return cached

    g, coins, fng = await asyncio.gather(
        _fetch_json(client, CG_GLOBAL_URL),
        _fetch_json(client, CG_MARKETS_URL),
        _fetch_json(client, FNG_URL),
    )

    market: dict = {"coins": [], "fng": None, "mcap_change_24h": None, "btc_dominance": None}

    if isinstance(g, dict):
        d = g.get("data", {}) or {}
        market["mcap_change_24h"] = d.get("market_cap_change_percentage_24h_usd")
        market["btc_dominance"] = (d.get("market_cap_percentage", {}) or {}).get("btc")

    if isinstance(coins, list):
        for c in coins:
            market["coins"].append({
                "symbol": (c.get("symbol") or "").upper(),
                "name":   c.get("name"),
                "price":  c.get("current_price"),
                "change_24h": c.get("price_change_percentage_24h"),
                "image":  c.get("image"),
            })

    if isinstance(fng, dict):
        arr = fng.get("data") or []
        if arr:
            f0 = arr[0]
            market["fng"] = {
                "value": int(f0.get("value", 0)),
                "label": f0.get("value_classification", ""),
            }

    _set_cache("market", market, MARKET_TTL)
    return market


# ── Public API ────────────────────────────────────────────────────────────────

VALID_CATEGORIES = ("all", "crypto", "casino", "esports")

_EMPTY_MARKET = {"coins": [], "fng": None, "mcap_change_24h": None, "btc_dominance": None}


def _ok(res) -> list:
    """Coerce a gather result (list | Exception | None) into a safe list."""
    if isinstance(res, list):
        return res
    if isinstance(res, BaseException):
        logger.warning("source failed: %s", type(res).__name__)
    return []


def _ok_dict(res) -> dict:
    """Coerce a gather result into a safe market dict."""
    if isinstance(res, dict):
        return res
    if isinstance(res, BaseException):
        logger.warning("market failed: %s", type(res).__name__)
    return dict(_EMPTY_MARKET)


async def get_news(category: str = "all", limit: int = 40) -> dict:
    """Return {items, market, updated_at}. Cached; fails soft on dead feeds."""
    if category not in VALID_CATEGORIES:
        category = "all"

    cache_key = f"news:{category}:{limit}"
    cached = _cached(cache_key)
    if cached is not None:
        return cached

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=True) as client:
        # return_exceptions=True is the key safety net: one failing source can
        # NEVER blow up the whole response (that's what was emptying All/Esports).
        if category == "all":
            crypto, casino, es_rss, es_vlr, market = await asyncio.gather(
                _fetch_rss_category(client, "crypto"),
                _fetch_rss_category(client, "casino"),
                _fetch_rss_category(client, "esports"),
                _fetch_esports(client),
                _fetch_market(client),
                return_exceptions=True,
            )
            items = _ok(crypto) + _ok(casino) + _ok(es_rss) + _ok(es_vlr)
            market = _ok_dict(market)
        elif category == "esports":
            es_rss, es_vlr, market = await asyncio.gather(
                _fetch_rss_category(client, "esports"),
                _fetch_esports(client),
                _fetch_market(client),
                return_exceptions=True,
            )
            items = _ok(es_rss) + _ok(es_vlr)
            market = _ok_dict(market)
        else:
            rss, market = await asyncio.gather(
                _fetch_rss_category(client, category),
                _fetch_market(client),
                return_exceptions=True,
            )
            items = _ok(rss)
            market = _ok_dict(market)

    # newest first, dedupe by url, cap
    seen: set[str] = set()
    deduped: list[dict] = []
    for it in sorted(items, key=lambda x: x["published_at"], reverse=True):
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        deduped.append(it)
        if len(deduped) >= limit:
            break

    payload = {
        "items":      deduped,
        "market":     market,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    # short TTL if everything failed, so we retry soon instead of caching emptiness
    _set_cache(cache_key, payload, NEWS_TTL if deduped else 60)
    return payload


# ══════════════════════════════════════════════════════════════════════════════
#  Telegram-форматтер ленты (для бота). Чистый текст → Markdown V1.
# ══════════════════════════════════════════════════════════════════════════════

def _rel_time(iso: str, lang: str) -> str:
    """ISO → 'now' / '5m' / '3h' / '2d' (локализован только 'now')."""
    now_word = {"ru": "сейчас", "es": "ahora"}.get(lang, "now")
    try:
        ts = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        diff = (datetime.now(timezone.utc) - ts).total_seconds()
    except Exception:
        return ""
    if diff < 60:
        return now_word
    m = int(diff // 60)
    if m < 60:
        return f"{m}m"
    h = m // 60
    if h < 24:
        return f"{h}h"
    return f"{h // 24}d"


def _news_safe(text: str) -> str:
    """Заголовок безопасный для Markdown-ссылки: убираем скобки/звёзды/нижние подчёркивания."""
    if not text:
        return ""
    for ch in ("[", "]", "(", ")", "*", "_", "`"):
        text = text.replace(ch, " ")
    return " ".join(text.split()).strip()


def _news_url(url: str) -> str:
    """Экранируем символы, ломающие [text](url) в MarkdownV1."""
    return (url or "").replace("_", "%5F").replace("(", "%28").replace(")", "%29")


def _fng_face(value: int) -> str:
    if value >= 75:
        return "🤑"
    if value >= 55:
        return "🙂"
    if value >= 45:
        return "😐"
    if value >= 25:
        return "😬"
    return "😱"


def _market_line(market: dict) -> str:
    if not market:
        return ""
    bits: list[str] = []
    fng = market.get("fng")
    if isinstance(fng, dict) and fng.get("value") is not None:
        v = int(fng["value"])
        bits.append(f"{_fng_face(v)} F&G {v}")
    for c in (market.get("coins") or [])[:3]:
        sym = c.get("symbol") or ""
        price = c.get("price")
        chg = c.get("change_24h")
        if not sym or price is None:
            continue
        if price >= 1000:
            ptxt = f"${round(price):,}"
        elif price >= 1:
            ptxt = f"${price:.2f}"
        else:
            ptxt = f"${price:.4f}"
        if chg is None:
            bits.append(f"{sym} {ptxt}")
        else:
            arrow = "▲" if chg >= 0 else "▼"
            bits.append(f"{sym} {ptxt} {arrow}{abs(chg):.1f}%")
    return "  ·  ".join(bits)


def format_news_message(items: list[dict], market: dict | None = None,
                        lang: str = "en", max_items: int = 6) -> str:
    """Рендер ленты новостей как Telegram Markdown-дайджеста. Пусто → ''."""
    lines: list[str] = []
    mkt = _market_line(market or {})
    if mkt:
        lines.append(f"_{mkt}_\n")
    if not items:
        return ""
    for it in items[:max_items]:
        title = _news_safe(it.get("title", ""))
        if not title:
            continue
        url = _news_url(it.get("url", ""))
        src = it.get("source", "")
        when = _rel_time(it.get("published_at", ""), lang)
        meta = " · ".join(x for x in (src, when) if x)
        if url:
            lines.append(f"• [{title}]({url})\n  {meta}")
        else:
            lines.append(f"• {title}\n  {meta}")
    return "\n\n".join(lines)
