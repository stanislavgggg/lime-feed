"""
onboarding.py — Kinetic Feed (news & live scores)

3-step conversational onboarding. Kit asks questions, AI extracts
structured preferences from any answer in any language.

Step 1: Sport preference  (football / esports / both)
Step 2: Leagues / games   (specific leagues or esports titles)
Step 3: Teams + style     (favourite teams, value vs picks vs live)

After step 3 → save preferences → show bridge to Coinplay.

Preferences are used to:
  - Filter daily picks and broadcasts
  - Personalize AI responses
  - Personalize Mini App (later)
"""
import json, logging
import httpx
from config import ANTHROPIC_KEY, AI_MODEL
from storage import get_user, update_user, update_preferences, append_history

logger = logging.getLogger(__name__)
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

# ── Onboarding questions (shown to user) ──────────────────────────────────────

QUESTIONS = {
    "en": [
        ("📰 *Which topics should I prioritise?*\n\n"
         "Crypto, casino/iGaming, esports, football — pick what you actually follow "
         "(one or several)."),
        ("Got it. *Any teams, leagues or coins to highlight?*\n\n"
         "La Liga, CS2, BTC, your club — I'll surface those first in scores and alerts. "
         "Or just say “skip”."),
    ],
    "ru": [
        ("📰 *Какие темы ставить в приоритет?*\n\n"
         "Крипта, казино/iGaming, киберспорт, футбол — выбери, за чем реально следишь "
         "(одну или несколько)."),
        ("Понял. *Какие команды, лиги или монеты выделять?*\n\n"
         "Ла Лига, CS2, BTC, твой клуб — поставлю их первыми в счёте и алертах. "
         "Или напиши «пропустить»."),
    ],
    "es": [
        ("📰 *¿Qué temas priorizo?*\n\n"
         "Cripto, casino/iGaming, esports, fútbol — elegí lo que realmente seguís "
         "(uno o varios)."),
        ("Perfecto. *¿Equipos, ligas o monedas para destacar?*\n\n"
         "La Liga, CS2, BTC, tu club — los pongo primeros en resultados y alertas. "
         "O escribí “saltar”."),
    ],
}

DONE_MSG = {
    "en": ("🎯 *Sorted — profile's set up.*\n\n"
           "I'll lead the feed with what you actually follow. No noise, just the signals "
           "that matter.\n\n"
           "Now — where the full feed lives 👇"),
    "ru": ("🎯 *Готово — профиль настроен.*\n\n"
           "Буду ставить в начало ленты то, за чем ты следишь. Без шума — только нужные "
           "сигналы.\n\n"
           "А теперь — где живёт полный фид 👇"),
    "es": ("🎯 *Listo — perfil configurado.*\n\n"
           "Voy a abrir el feed con lo que realmente seguís. Sin ruido, solo las señales "
           "que importan.\n\n"
           "Ahora — dónde vive el feed completo 👇"),
}


# ── AI preference extractor ───────────────────────────────────────────────────

async def extract_preferences(user_message: str, step: int, lang: str) -> dict:
    """
    Given user's answer at onboarding step N,
    extract structured preferences as JSON.
    Returns partial dict — only fields that were mentioned.
    """
    step_context = {
        0: "User answered which content topics they follow (crypto, casino, esports, football).",
        1: "User answered which teams, leagues or coins to highlight (may say skip).",
    }.get(step, "")

    prompt = f"""Extract content preferences from this user message.
Context: {step_context}
Message: "{user_message}"

Return ONLY valid JSON with any of these fields that are mentioned:
{{
  "topics": ["crypto" | "casino" | "esports" | "football"],
  "leagues": ["league names as strings"],
  "games": ["cs2" | "lol" | "dota2" | "valorant" | "r6" | "ow2"],
  "teams": ["team, club, or coin tickers as strings"]
}}

Rules:
- Only include fields actually mentioned in the message
- "topics" maps interests to: crypto, casino (incl. iGaming/gambling), esports, football
- Normalize league names: "libertadores" → "Copa Libertadores", "epl" → "Premier League"
- Normalize game names to slugs: "counter strike" → "cs2", "league of legends" → "lol"
- Coin tickers (BTC, ETH, SOL) go in "teams"
- If the user says skip / nothing / no → return empty object {{}}
- Return empty object {{}} if nothing extractable
- NO markdown, NO explanation, ONLY the JSON object"""

    headers = {
        "x-api-key":         ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    payload = {
        "model":      AI_MODEL,
        "max_tokens": 200,
        "messages":   [{"role": "user", "content": prompt}],
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(ANTHROPIC_URL, headers=headers, json=payload)
            resp.raise_for_status()
            raw = resp.json()["content"][0]["text"].strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)
    except Exception as e:
        logger.error(f"Preference extraction error: {e}")
        return {}


# ── Onboarding step runner ────────────────────────────────────────────────────

async def process_onboarding_answer(
    user_id: int,
    user_message: str,
    step: int,
    lang: str,
) -> tuple[str | None, bool]:
    """
    Process user's answer for current onboarding step.
    Extracts preferences, saves them.
    Returns (next_question_text | None, onboarding_complete).
    next_question_text = None means onboarding is complete → show bridge.
    """
    # Extract preferences from this answer
    prefs = await extract_preferences(user_message, step, lang)
    if prefs:
        # Merge lists, don't overwrite
        u = get_user(user_id)
        existing = u.get("preferences", {})
        merged = {}
        for field in ("topics", "leagues", "games", "teams"):
            old = existing.get(field) or []
            new = prefs.get(field) or []
            merged[field] = list(dict.fromkeys(old + new))  # deduplicate, preserve order
        update_preferences(user_id, **merged)
        logger.info(f"User {user_id} prefs updated step={step}: {merged}")

    next_step = step + 1
    questions  = QUESTIONS.get(lang, QUESTIONS["en"])

    if next_step < len(questions):
        return questions[next_step], False
    else:
        return None, True  # onboarding complete


def get_first_question(lang: str) -> str:
    """First onboarding question (step 0 → shown after /start hook)."""
    return QUESTIONS.get(lang, QUESTIONS["en"])[0]


def format_preferences_summary(prefs: dict, lang: str) -> str:
    """Human-readable summary of saved preferences."""
    parts = []
    if prefs.get("topics"):
        label = "Topics" if lang == "en" else ("Темы" if lang == "ru" else "Temas")
        parts.append(f"{label}: *{', '.join(prefs['topics'])}*")
    if prefs.get("leagues"):
        label = "Leagues" if lang == "en" else ("Лиги" if lang == "ru" else "Ligas")
        parts.append(f"{label}: *{', '.join(prefs['leagues'])}*")
    if prefs.get("games"):
        label = "Games" if lang == "en" else ("Дисциплины" if lang == "ru" else "Juegos")
        parts.append(f"{label}: *{', '.join(g.upper() for g in prefs['games'])}*")
    if prefs.get("teams"):
        label = "Watching" if lang == "en" else ("Слежу за" if lang == "ru" else "Sigo")
        parts.append(f"{label}: *{', '.join(prefs['teams'])}*")

    if not parts:
        return ""
    header = ("📋 *Your profile:*\n" if lang == "en"
              else ("📋 *Твой профиль:*\n" if lang == "ru" else "📋 *Tu perfil:*\n"))
    return header + "\n".join(f"• {p}" for p in parts)
