"""
livescore.py — Kinetic Feed (news & live scores)

Football:  Free API Live Football Data (RapidAPI)
           Host: free-api-live-football-data.p.rapidapi.com
Esports:   ESportApi (RapidAPI) — esportapi1.p.rapidapi.com
           Endpoint: /api/esport/matches/live  → { events: [...] }
           Endpoint: /api/esport/matches/scheduled/date/YYYY-MM-DD → { events: [...] }
"""
import asyncio, logging, time
from datetime import datetime, timezone, timedelta
import httpx
from config import PANDASCORE_KEY, RAPIDAPI_KEY, FOOTBALL_API_HOST, GAME_DISPLAY

logger = logging.getLogger(__name__)

# ── ESportApi (RapidAPI) ──────────────────────────────────────────────────────
ESPORTAPI_BASE = "https://esportapi1.p.rapidapi.com"
ESPORTAPI_HOST = "esportapi1.p.rapidapi.com"

# ── Football API (RapidAPI) ───────────────────────────────────────────────────
FOOTBALL_BASE  = f"https://{FOOTBALL_API_HOST}"

_cache: dict = {}
CACHE_TTL = 300  # 5 min


def _cached(key):
    e = _cache.get(key)
    if e and time.time() - e["ts"] < CACHE_TTL:
        return e["data"]
    return None

def _set_cache(key, data):
    _cache[key] = {"ts": time.time(), "data": data}


# ── Football ──────────────────────────────────────────────────────────────────

def _football_headers():
    return {
        "x-rapidapi-key":  RAPIDAPI_KEY,
        "x-rapidapi-host": FOOTBALL_API_HOST,
        "Content-Type":    "application/json",
    }

async def _football_get(path: str, params: dict = {}) -> dict | None:
    if not RAPIDAPI_KEY:
        return None
    url = f"{FOOTBALL_BASE}{path}"
    logger.info(f"Football API → GET {url}")
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(url, headers=_football_headers(), params=params)
            logger.info(f"Football API ← {r.status_code} ({len(r.content)} bytes)")
            r.raise_for_status()
            data = r.json()
            logger.info(f"Football API keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return data
    except httpx.HTTPStatusError as e:
        logger.error(f"Football API HTTP {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"Football API {path} {type(e).__name__}: {e}")
        return None

def _parse_football_live(data: dict) -> list[dict]:
    matches = []
    for m in (data.get("response") or {}).get("live") or []:
        home = m.get("home") or {}
        away = m.get("away") or {}
        matches.append({
            "game":     "Football ⚽",
            "team1":    home.get("name") or home.get("longName", "?"),
            "team2":    away.get("name") or away.get("longName", "?"),
            "score1":   home.get("score"),
            "score2":   away.get("score"),
            "status":   "LIVE 🔴",
            "league":   str(m.get("leagueId", "")),
            "begin_at": m.get("time", ""),
            "winner":   None,
            "format":   "90'",
        })
    return matches

async def get_live_football() -> tuple[list[dict], bool]:
    key = "football_live"
    cached = _cached(key)
    if cached is not None:
        return cached
    data = await _football_get("/football-current-live")
    if data is None:
        return _mock_live_football(), True
    matches = _parse_football_live(data)
    _set_cache(key, (matches, False))
    return matches, False

async def get_today_football() -> tuple[list[dict], bool]:
    """Today's football — uses live endpoint.
    Returns empty real list (not mock) when API works but no matches now.
    """
    key = "football_today"
    cached = _cached(key)
    if cached is not None:
        return cached
    data = await _football_get("/football-current-live")
    if data is None:
        return _mock_today_football(), True
    # API responded — even if empty, it's real data (no matches right now)
    matches = _parse_football_live(data)
    result = (matches, False)
    _set_cache(key, result)
    return result


# ── ESportApi (RapidAPI) ──────────────────────────────────────────────────────

# Map category slugs/names from API → display names
# ESportApi uses various slugs — cover all variants
CATEGORY_TO_GAME = {
    # CS2 / Counter-Strike
    "csgo": "CS2", "cs-go": "CS2", "counter-strike": "CS2",
    "cs2": "CS2", "counterstrikecsgo": "CS2", "counterstrike": "CS2",
    # LoL
    "lol": "LoL", "league-of-legends": "LoL", "leagueoflegends": "LoL",
    "league_of_legends": "LoL",
    # Dota 2
    "dota2": "Dota 2", "dota-2": "Dota 2", "dota_2": "Dota 2",
    # Valorant
    "valorant": "Valorant",
    # Overwatch
    "overwatch": "Overwatch 2", "ow2": "Overwatch 2", "overwatch-2": "Overwatch 2",
    # Rainbow Six
    "r6siege": "Rainbow Six", "rainbow-six": "Rainbow Six", "rainbowsix": "Rainbow Six",
    # Rocket League
    "rocketleague": "Rocket League", "rocket-league": "Rocket League",
    # StarCraft
    "starcraft2": "StarCraft 2", "sc2": "StarCraft 2",
}

# Also map by tournament/league name keywords when slug fails
TOURNAMENT_KEYWORDS = {
    "cs asia": "CS2", "blast premier": "CS2", "pgl": "CS2", "cct": "CS2",
    "esl": "CS2",  # mostly CS2, handle LoL separately
    "lck": "LoL", "lpl": "LoL", "lec": "LoL", "msi": "LoL", "worlds": "LoL",
    "ti ": "Dota 2", "the international": "Dota 2", "esl one": "Dota 2",
    "vct": "Valorant", "champions": "Valorant",
    "nodwin": "CS2", "united21": "CS2",
}

async def _esportapi_get(endpoint: str, params: dict = {}) -> dict | None:
    """ESportApi via RapidAPI — esportapi1.p.rapidapi.com
    Railway allows *.rapidapi.com egress — confirmed working for football.
    """
    if not RAPIDAPI_KEY:
        logger.warning("ESportApi: RAPIDAPI_KEY not set")
        return None
    url = f"{ESPORTAPI_BASE}{endpoint}"
    logger.info(f"ESportApi → GET {url}")
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(url, headers={
                "x-rapidapi-key":  RAPIDAPI_KEY,
                "x-rapidapi-host": ESPORTAPI_HOST,
                "Content-Type":    "application/json",
            }, params=params)
            logger.info(f"ESportApi ← {r.status_code} ({len(r.content)} bytes)")
            r.raise_for_status()
            data = r.json()
            logger.info(f"ESportApi events: {len(data.get('events', []))}")
            return data
    except httpx.HTTPStatusError as e:
        logger.error(f"ESportApi HTTP {e.response.status_code}: {e.response.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"ESportApi {endpoint} {type(e).__name__}: {e}")
        return None

def _parse_esportapi_match(m: dict, status: str) -> dict:
    """Parse ESportApi response event.

    Real structure verified from RapidAPI playground:
    {
      homeTeam: { name: "NAVI", slug: "natus-vincere" },
      awayTeam: { name: "Vitality", slug: "team-vitality" },
      homeScore: { current: 1, display: 1 },
      awayScore: { current: 0, display: 0 },
      tournament: {
        name: "CS Asia Championships",
        category: { slug: "csgo", name: "Counter Strike" }
      },
      startTimestamp: 1716200000,
      bestOf: 3
    }
    """
    team1  = (m.get("homeTeam") or {}).get("name", "TBD")
    team2  = (m.get("awayTeam") or {}).get("name", "TBD")
    score1 = (m.get("homeScore") or {}).get("current")
    score2 = (m.get("awayScore") or {}).get("current")

    # Define league first — used in game detection fallback below
    league = (m.get("tournament") or {}).get("name", "")

    # Game from category slug (most reliable field)
    cat = (m.get("tournament") or {}).get("category") or {}
    cat_slug = cat.get("slug", "").lower().replace("-", "").replace("_", "").replace(" ", "")
    game = CATEGORY_TO_GAME.get(cat_slug)

    if not game:
        # Try original slug with hyphens
        cat_slug_orig = cat.get("slug", "").lower()
        game = CATEGORY_TO_GAME.get(cat_slug_orig)

    if not game:
        # Try category name
        cat_name = cat.get("name", "").lower()
        game = CATEGORY_TO_GAME.get(cat_name)

    if not game:
        # Try tournament name keywords
        t_name = league.lower() if league else ""
        for keyword, g in TOURNAMENT_KEYWORDS.items():
            if keyword in t_name:
                game = g
                break

    if not game:
        # Last resort: use category name as-is
        game = cat.get("name", "Esports")

    fmt      = f"Bo{m['bestOf']}" if m.get("bestOf") else "Bo3"
    ts       = m.get("startTimestamp", 0)
    begin_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""

    return {
        "game":     game or "Esports",
        "team1":    team1,
        "team2":    team2,
        "score1":   score1,
        "score2":   score2,
        "status":   status,
        "league":   league,
        "begin_at": begin_at,
        "winner":   None,
        "format":   fmt,
    }

async def _get_live_esports_esportapi() -> list[dict]:
    """GET /api/esport/matches/live → { events: [...] }"""
    data = await _esportapi_get("/api/esport/matches/live")
    if not data:
        return []
    events = data.get("events") or []
    if not events:
        logger.info("ESportApi live: 0 events")
        return []
    logger.info(f"ESportApi live: {len(events)} events")
    parsed = []
    for e in events[:20]:
        try:
            parsed.append(_parse_esportapi_match(e, "LIVE 🔴"))
        except Exception as ex:
            logger.warning(f"ESportApi parse error (live): {ex}")
    return parsed

async def _get_upcoming_esports_esportapi() -> list[dict]:
    """Fetch upcoming/scheduled esports matches from ESportApi.

    Confirmed working endpoints (verified against RapidAPI playground):
      /api/esport/matches/scheduled/date/{YYYY-MM-DD}  → today's schedule
      /api/esport/matches/live                          → also contains
                                                          not-yet-started rounds

    Endpoints that DO NOT exist (return 404):
      /api/esport/matches/schedule   ← removed
      /api/esport/matches/upcoming   ← removed
    """
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    all_events: list[dict] = []

    for date_str in [today, tomorrow]:
        endpoint = f"/api/esport/matches/scheduled/date/{date_str}"
        data = await _esportapi_get(endpoint)
        if not data:
            continue
        events = data.get("events") or []
        logger.info(f"ESportApi scheduled/{date_str}: {len(events)} events")
        all_events.extend(events)
        if len(all_events) >= 30:
            break

    if all_events:
        parsed = []
        for e in all_events[:30]:
            try:
                parsed.append(_parse_esportapi_match(e, "upcoming"))
            except Exception as ex:
                logger.warning(f"ESportApi parse error (upcoming): {ex}")
        if parsed:
            return parsed

    # Fallback: /api/esport/matches/live also includes upcoming rounds in a series
    data = await _esportapi_get("/api/esport/matches/live")
    if data:
        events = data.get("events") or []
        upcoming = [e for e in events if not (e.get("homeScore") or e.get("awayScore"))]
        if upcoming:
            logger.info(f"ESportApi upcoming (via live): {len(upcoming)} events")
            parsed = []
            for e in upcoming[:20]:
                try:
                    parsed.append(_parse_esportapi_match(e, "upcoming"))
                except Exception as ex:
                    logger.warning(f"ESportApi parse error (upcoming/live): {ex}")
            if parsed:
                return parsed

    return []


# ── PandaScore fallback (if ESportApi blocked) ────────────────────────────────

async def _pandascore_get(endpoint: str, params: dict = {}) -> list | None:
    if not PANDASCORE_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"https://api.pandascore.co{endpoint}",
                headers={"Authorization": f"Bearer {PANDASCORE_KEY}"},
                params=params,
            )
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.error(f"PandaScore {endpoint}: {e}")
        return None

def _fmt_esports(m: dict, status: str) -> dict:
    opps  = m.get("opponents") or []
    team1 = (opps[0].get("opponent") or {}).get("name", "TBD") if len(opps) > 0 else "TBD"
    team2 = (opps[1].get("opponent") or {}).get("name", "TBD") if len(opps) > 1 else "TBD"
    res   = m.get("results") or []
    s1    = res[0].get("score") if len(res) > 0 else None
    s2    = res[1].get("score") if len(res) > 1 else None
    slug  = (m.get("videogame") or {}).get("slug", "")
    game  = GAME_DISPLAY.get(slug, slug.upper() or "Esports")
    return {
        "game": game, "team1": team1, "team2": team2,
        "score1": s1, "score2": s2, "status": status,
        "begin_at": m.get("begin_at", ""),
        "league": (m.get("league") or {}).get("name", ""),
        "winner": None, "format": "Bo3",
    }


# ── Public esports getters ────────────────────────────────────────────────────

async def get_live_esports() -> tuple[list[dict], bool]:
    key = "esports_live"
    cached = _cached(key)
    if cached is not None:
        return cached

    matches = await _get_live_esports_esportapi()
    if matches:
        _set_cache(key, (matches, False))
        return matches, False

    return _mock_live_esports(), True

async def get_upcoming_esports(hours: int = 24) -> tuple[list[dict], bool]:
    key = f"esports_upcoming_{hours}"
    cached = _cached(key)
    if cached is not None:
        return cached

    matches = await _get_upcoming_esports_esportapi()
    if matches:
        _set_cache(key, (matches, False))
        return matches, False

    return _mock_upcoming_esports(), True

async def get_recent_esports_results(limit: int = 5) -> tuple[list[dict], bool]:
    key = "esports_recent"
    cached = _cached(key)
    if cached is not None:
        return cached
    return _mock_results(), True


# ── Combined context for AI + display ─────────────────────────────────────────

async def fetch_match_context() -> dict:
    (live_e, mock_le), (live_f, mock_lf), (up_e, mock_ue), (today_f, mock_tf) = await asyncio.gather(
        get_live_esports(),
        get_live_football(),
        get_upcoming_esports(24),
        get_today_football(),
    )
    # Real data = API responded (even if 0 results), mock = API failed/fallback
    real_live     = ([] if mock_le else live_e) + ([] if mock_lf else live_f)
    real_upcoming = ([] if mock_ue else up_e)   + ([] if mock_tf else today_f)

    # has_real_* = True if at least one source responded with real data (even empty)
    has_real_live     = not mock_le or not mock_lf
    has_real_upcoming = not mock_ue or not mock_tf

    # For display: prefer real matches; if real is empty but API worked → show empty state
    # Only fall back to mock display if ALL sources failed
    display_live     = real_live     if has_real_live     else live_e + live_f
    display_upcoming = real_upcoming if has_real_upcoming else up_e + today_f

    return {
        "live":           real_live,
        "upcoming":       real_upcoming,
        "has_real":       bool(real_live or real_upcoming),
        "has_real_live":  has_real_live,
        "has_real_upcoming": has_real_upcoming,
        "for_display": {
            "live":     display_live,
            "upcoming": display_upcoming,
        },
    }


# ── Formatters ─────────────────────────────────────────────────────────────────

def format_livescore_message(matches: list[dict], lang: str, is_mock: bool = False) -> str:
    if is_mock:
        return (
            "📡 No live matches right now — I'll ping you when something kicks off."
            if lang == "en" else
            "📡 Sin partidos en vivo ahora mismo — te aviso cuando empiece algo."
        )
    if not matches:
        return (
            "📡 *Live right now:*\n\nAll quiet — no matches in progress. Check back soon or tap 📅 Today for upcoming."
            if lang == "en" else
            "📡 *En vivo ahora:*\n\nTodo tranquilo — no hay partidos en curso. Revisá pronto o tocá 📅 Hoy para ver los próximos."
        )
    lines = []
    for m in matches[:8]:
        score = f" *{m['score1']}–{m['score2']}*" if m.get("score1") is not None else ""
        line  = f"🔴 *{m['game']}* — {m['team1']} vs {m['team2']}{score}"
        if m.get("league"):
            line += f"\n   _{m['league']}_"
        lines.append(line)
    header = "📡 *Live right now:*" if lang == "en" else "📡 *En vivo ahora:*"
    return header + "\n\n" + "\n\n".join(lines)

def format_upcoming_message(matches: list[dict], lang: str, is_mock: bool = False) -> str:
    if is_mock or not matches:
        return (
            "📅 No fixtures data yet — check back soon."
            if lang == "en" else
            "📅 Sin datos de fixtures aún — volvé pronto."
        )
    lines = []
    for m in matches[:8]:
        begin = ""
        if m.get("begin_at"):
            try:
                dt    = datetime.fromisoformat(str(m["begin_at"]).replace("Z", "+00:00"))
                begin = f" @ {dt.strftime('%H:%M UTC')}"
            except Exception:
                begin = f" @ {m['begin_at']}"
        fmt  = f" ({m['format']})" if m.get("format") else ""
        line = f"🕐 *{m['game']}*{fmt} — {m['team1']} vs {m['team2']}{begin}"
        if m.get("league"):
            line += f"\n   _{m['league']}_"
        lines.append(line)
    header = "📅 *Today's matches:*" if lang == "en" else "📅 *Partidos de hoy:*"
    return header + "\n\n" + "\n\n".join(lines)

def format_results_message(matches: list[dict], lang: str, is_mock: bool = False) -> str:
    if is_mock or not matches:
        return "No recent results." if lang == "en" else "Sin resultados recientes."
    lines = []
    for m in matches[:6]:
        score      = f" {m['score1']}–{m['score2']}" if m.get("score1") is not None else ""
        winner_str = f" → *{m['winner']} wins*" if m.get("winner") else ""
        line       = f"✅ *{m['game']}* — {m['team1']} vs {m['team2']}{score}{winner_str}"
        if m.get("league"):
            line += f"\n   _{m['league']}_"
        lines.append(line)
    header = "📊 *Recent results:*" if lang == "en" else "📊 *Resultados recientes:*"
    return header + "\n\n" + "\n\n".join(lines)


# ── Mock data (display only — never passed to AI) ─────────────────────────────

def _mock_live_esports() -> list[dict]:
    return [
        {"game": "CS2", "team1": "NAVI", "team2": "Vitality", "score1": 1, "score2": 0,
         "status": "LIVE 🔴", "league": "PGL Major", "winner": None, "format": "Bo3", "begin_at": ""},
        {"game": "Dota 2", "team1": "Team Spirit", "team2": "Gaimin Gladiators", "score1": 0, "score2": 1,
         "status": "LIVE 🔴", "league": "ESL One", "winner": None, "format": "Bo3", "begin_at": ""},
    ]

def _mock_upcoming_esports() -> list[dict]:
    return [
        {"game": "LoL", "team1": "T1", "team2": "Gen.G", "score1": None, "score2": None,
         "status": "upcoming", "league": "LCK", "winner": None, "format": "Bo5", "begin_at": ""},
        {"game": "Valorant", "team1": "Sentinels", "team2": "LOUD", "score1": None, "score2": None,
         "status": "upcoming", "league": "VCT Americas", "winner": None, "format": "Bo3", "begin_at": ""},
        {"game": "CS2", "team1": "FaZe", "team2": "G2", "score1": None, "score2": None,
         "status": "upcoming", "league": "BLAST Premier", "winner": None, "format": "Bo3", "begin_at": ""},
    ]

def _mock_results() -> list[dict]:
    return [
        {"game": "CS2", "team1": "NAVI", "team2": "NIP", "score1": 2, "score2": 0,
         "status": "finished", "league": "BLAST", "winner": "NAVI", "format": "Bo3", "begin_at": ""},
    ]

def _mock_live_football() -> list[dict]:
    return [
        {"game": "Football ⚽", "team1": "Real Madrid", "team2": "Barcelona",
         "score1": 1, "score2": 1, "status": "LIVE 🔴", "league": "La Liga", "begin_at": "", "winner": None, "format": "90'"},
    ]

def _mock_today_football() -> list[dict]:
    return [
        {"game": "Football ⚽", "team1": "Man City", "team2": "Arsenal",
         "score1": None, "score2": None, "status": "upcoming", "league": "Premier League", "begin_at": "", "winner": None, "format": "90'"},
        {"game": "Football ⚽", "team1": "River Plate", "team2": "Boca Juniors",
         "score1": None, "score2": None, "status": "upcoming", "league": "Primera Division AR", "begin_at": "", "winner": None, "format": "90'"},
    ]
