"""
ai_agent.py — Kinetic Feed (news & live scores)

Preferences injected into every prompt for personalization.
Two modes: onboarding (structured extraction) and assistant (free conversation).
Anti-hallucination: only real match data passed, never mock.
"""
import logging, re
import httpx
from config import ANTHROPIC_KEY, AI_MODEL, AI_MAX_TOKENS, OFFER, COINPLAY_REG_URL, CHANNEL_HANDLE
from brand import BRAND

logger = logging.getLogger(__name__)
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

INTENT_RE  = re.compile(r'\[INTENT:([^\]]+)\]')
BARRIER_RE = re.compile(r'\[BARRIER:([^\]]+)\]')
STAGE_RE   = re.compile(r'\[NEXT:([^\]]+)\]')


def _prefs_str(prefs: dict) -> str:
    if not prefs or not any(prefs.values()):
        return "No preferences collected yet."
    parts = []
    if prefs.get("topics"):
        parts.append(f"Topics: {', '.join(prefs['topics'])}")
    if prefs.get("sport"):
        parts.append(f"Sport: {prefs['sport']}")
    if prefs.get("leagues"):
        parts.append(f"Leagues: {', '.join(prefs['leagues'])}")
    if prefs.get("games"):
        parts.append(f"Esports games: {', '.join(prefs['games'])}")
    if prefs.get("teams"):
        parts.append(f"Favourite teams: {', '.join(prefs['teams'])}")
    return " | ".join(parts) if parts else "No preferences collected yet."


def _match_ctx(real_live: list, real_upcoming: list) -> str:
    if not real_live and not real_upcoming:
        return "NO MATCH DATA AVAILABLE — do not invent any matches, teams, or scores."
    lines = []
    if real_live:
        lines.append("LIVE NOW (real):")
        for m in real_live[:5]:
            score = f" ({m['score1']}–{m['score2']})" if m.get("score1") is not None else ""
            lines.append(f"  {m['game']}: {m['team1']} vs {m['team2']}{score} | {m.get('league','')}")
    if real_upcoming:
        lines.append("UPCOMING TODAY (real):")
        for m in real_upcoming[:8]:
            fmt = f" ({m.get('format','')})" if m.get("format") else ""
            lines.append(f"  {m['game']}{fmt}: {m['team1']} vs {m['team2']} | {m.get('league','')}")
    return "\n".join(lines)


def _assistant_system(lang: str, state: str, prefs: dict, real_live: list, real_upcoming: list) -> str:
    from brand import BRAND, CTAMode
    is_channel = BRAND.cta.mode is CTAMode.CHANNEL

    lang_instr = {
        "ru": "Отвечай по-русски, живым разговорным тоном, коротко.",
        "es": "Respond in Spanish (Latin American, casual).",
    }.get(lang, "Respond in English (casual, direct).")
    persona = BRAND.character.persona.format(
        name=BRAND.character.name,
        role=BRAND.character.role,
        brand=BRAND.display_name,
        partner=BRAND.cta.partner_name or BRAND.display_name,
    )

    if is_channel:
        goal_block = (
            f"GOAL: довести человека до ПОДПИСКИ на канал {CHANNEL_HANDLE or BRAND.display_name}, "
            f"где идёт полный фид: новости, мгновенные алерты и пуши со счётом. Вход бесплатный.\n"
            "СТРОГО: ты новостной/score-ведущий, а не типстер. Не давай беттинг-советов, "
            "не рекомендуй ставки/депозиты/покупки, не обещай выигрыши, не подавай "
            "коэффициенты как призыв ставить."
        )
        role_lines = (
            "- кратко отвечай на вопросы по новостям (крипта/казино/киберспорт/футбол) и live-счёту\n"
            "- естественно зови в канал за полным фидом и алертами, без давления\n"
            "- у пользователя есть кнопки меню (Live / News / Upcoming) — не дублируй их\n"
            "- держись в пределах 150 слов"
        )
    else:
        offer = (
            f"100% bonus up to {OFFER['bonus_max']} USDT + {OFFER['free_spins']} free spins, "
            f"min {OFFER['min_deposit']} USDT, {OFFER['cashback_pct']}% cashback, 40+ cryptos"
        )
        goal_block = f"COINPLAY: {offer} | {COINPLAY_REG_URL} | Curacao licensed, 2022"
        role_lines = (
            "- Answer questions about sports, betting strategy, crypto\n"
            "- Mention Coinplay naturally when relevant, don't push hard\n"
            "- User has menu buttons for live scores/picks — don't replicate those\n"
            "- Keep responses under 160 words"
        )

    return f"""{persona}
{lang_instr}

USER PROFILE (personalize responses to this):
{_prefs_str(prefs)}

REAL MATCH DATA (ONLY reference these — never invent):
{_match_ctx(real_live, real_upcoming)}

{goal_block}

ANTI-HALLUCINATION:
- NEVER invent match names, teams, scores, odds, or results
- NEVER fabricate team statistics, win rates, or player names
- If no match data → talk strategy/analysis in general terms ONLY
- NEVER mention a specific match not in the data above
- If you are unsure about a team's recent form → say "based on recent tournament results" not invented stats

PERSONALIZATION RULES:
- Reference user's preferred leagues/teams/games when relevant
- If they follow Libertadores → mention South American angles
- If they follow CS2 → reference current meta, major tournaments
- Tailor examples to their profile

CURRENT STATE: {state}

ROLE:
{role_lines}

INTENT TAGS (prepend):
[INTENT:esports_fan|football_fan|platform_curious|deposit_ready|ftd_confirmed|objection|just_browsing]
[NEXT:warmup|bridge|converting|deposited]
"""


async def get_ai_response(
    user_message: str,
    lang: str,
    state: str,
    history: list,
    barriers: list,
    real_live: list = None,
    real_upcoming: list = None,
    prefs: dict = None,
) -> dict:
    system = _assistant_system(lang, state, prefs or {}, real_live or [], real_upcoming or [])
    messages = [{"role": e["role"], "content": e["content"]} for e in history[-12:]]
    messages.append({"role": "user", "content": user_message})

    headers = {
        "x-api-key":         ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    payload = {
        "model":      AI_MODEL,
        "max_tokens": AI_MAX_TOKENS,
        "system":     system,
        "messages":   messages,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(ANTHROPIC_URL, headers=headers, json=payload)
            resp.raise_for_status()
            raw = resp.json()["content"][0]["text"].strip()

        intent  = (INTENT_RE.search(raw)  or type("x",(),{"group":lambda s,i:"just_browsing"})()).group(1)
        barrier = (BARRIER_RE.search(raw) or type("x",(),{"group":lambda s,i:None})()).group(1)
        next_s  = (STAGE_RE.search(raw)   or type("x",(),{"group":lambda s,i:None})()).group(1)
        clean   = STAGE_RE.sub("", BARRIER_RE.sub("", INTENT_RE.sub("", raw))).strip()
        return {"text": clean, "intent": intent, "barrier": barrier, "next": next_s}

    except httpx.TimeoutException:
        logger.error("AI timeout")
        return _fallback(lang)
    except Exception as e:
        logger.error(f"AI error: {e}")
        return _fallback(lang)


def _fallback(lang: str) -> dict:
    return {
        "text": "📡 Give me a sec." if lang == "en" else "📡 Dame un segundo.",
        "intent": "just_browsing", "barrier": None, "next": None,
    }


async def detect_ftd(user_message: str, lang: str) -> bool:
    prompt = (
        f'Did this message confirm the user made a deposit or completed registration '
        f'on a gambling/crypto platform?\nMessage: "{user_message}"\nReply only: YES or NO'
    )
    headers = {
        "x-api-key":         ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    payload = {
        "model": AI_MODEL, "max_tokens": 10,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(ANTHROPIC_URL, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()["content"][0]["text"].strip().upper().startswith("YES")
    except Exception as e:
        logger.error(f"FTD detect: {e}")
        return False
