"""
copy_goalcast.py — пакет копирайта бренда GoalCast
===================================================
Персонаж: Diego — футбольный аналитик.
Воронка: ведём не в продукт, а на подписку в Telegram-канал (CTAMode.CHANNEL).
Тон: страстный, по делу, без хайпа. Языки: EN / ES.

Имена символов идентичны copy_metaplay.py — их подхватывает messages.py.
В channel-режиме {url} = ссылка на канал (config.COINPLAY_REG_URL → channel_url).
"""

# ── /start HOOK ───────────────────────────────────────────────────────────────
HOOK_CAPTION = {
    "en": (
        "⚽ *GoalCast — football reads, every matchday*\n\n"
        "I'm Diego, full-time football analyst. "
        "Form, head-to-head, travel fatigue, lineups — I track it all.\n\n"
        "Every day I share:\n"
        "• Live scores & real-time updates\n"
        "• Pre-match analysis with full reasoning\n"
        "• Early reads before kickoff\n\n"
        "Which leagues do you follow most?"
    ),
    "es": (
        "⚽ *GoalCast — lecturas de fútbol, cada jornada*\n\n"
        "Soy Diego, analista de fútbol a tiempo completo. "
        "Forma, head-to-head, cansancio de viaje, formaciones — sigo todo.\n\n"
        "Cada día comparto:\n"
        "• Resultados en vivo y actualizaciones en tiempo real\n"
        "• Análisis pre-partido con razonamiento completo\n"
        "• Lecturas tempranas antes del pitazo inicial\n\n"
        "¿Qué ligas seguís más?"
    ),
}

# ── Warmup ────────────────────────────────────────────────────────────────────
WARMUP_FOOTBALL = {
    "en": [
        "⚽ Most people follow the team they love. I follow the data — "
        "form, head-to-head, fixtures congestion. That's where the edge is.",
        "📊 Home/away splits swing matches more than the table suggests. "
        "Tracking them properly is half the read.",
        "💡 Midweek European nights wreck weekend form. "
        "Fatigue is the most underrated factor in football.",
    ],
    "es": [
        "⚽ La mayoría sigue al equipo que ama. Yo sigo los datos — "
        "forma, head-to-head, congestión de partidos. Ahí está la ventaja.",
        "📊 Las diferencias local/visitante mueven partidos más de lo que dice la tabla. "
        "Rastrearlas bien es la mitad de la lectura.",
        "💡 Las noches europeas de mitad de semana destruyen la forma del finde. "
        "El cansancio es el factor más subestimado del fútbol.",
    ],
}
# Алиас на случай обращения к esports-варианту (бренд футбольный — отдаём то же).
WARMUP_ESPORTS = WARMUP_FOOTBALL

# ── Bridge: приглашение в канал ───────────────────────────────────────────────
BRIDGE = {
    "en": (
        "🔑 *Where the full reads live*\n\n"
        "I post complete match breakdowns in the GoalCast channel — "
        "the deep ones I can't fit here.\n\n"
        "• Daily pre-match analysis\n"
        "• Early reads before kickoff\n"
        "• Results & post-match notes\n\n"
        "It's free. Want the link?"
    ),
    "es": (
        "🔑 *Donde viven las lecturas completas*\n\n"
        "Publico los análisis completos en el canal de GoalCast — "
        "los profundos que no entran acá.\n\n"
        "• Análisis pre-partido diario\n"
        "• Lecturas tempranas antes del pitazo\n"
        "• Resultados y notas post-partido\n\n"
        "Es gratis. ¿Te paso el link?"
    ),
}

# ── CTA: подписка на канал ────────────────────────────────────────────────────
CTA_REGISTER = {
    "en": (
        "👇 *Join the GoalCast channel — free*\n\n"
        "{url}\n\n"
        "Tap, subscribe, and you'll get every match breakdown the moment it drops. ⚽"
    ),
    "es": (
        "👇 *Unite al canal de GoalCast — gratis*\n\n"
        "{url}\n\n"
        "Tocá, suscribite y recibís cada análisis en el momento que sale. ⚽"
    ),
}

# ── «Подтверждение» (в channel-режиме = подписался) ───────────────────────────
FTD_CELEBRATION = {
    "en": (
        "🔥 *You're in*\n\n"
        "Notifications on so you don't miss the early reads. "
        "I post the day's slate every morning. ⚽"
    ),
    "es": (
        "🔥 *Estás adentro*\n\n"
        "Activá las notificaciones para no perderte las lecturas tempranas. "
        "Publico el programa del día cada mañana. ⚽"
    ),
}

# ── Repeat (в channel-режиме обычно выключено: funnel.repeat_enabled=False) ────
REPEAT_PUSH = {
    "en": [
        "⚽ Today's slate is up in the channel — check the early reads.",
        "📊 Post-match notes are live. Worth a look before tomorrow.",
        "📣 Haven't turned on notifications yet? You're missing the early reads.",
    ],
    "es": [
        "⚽ El programa de hoy está en el canal — mirá las lecturas tempranas.",
        "📊 Las notas post-partido ya están. Vale la pena antes de mañana.",
        "📣 ¿Todavía no activaste notificaciones? Te perdés las lecturas tempranas.",
    ],
}

# ── Возражения ────────────────────────────────────────────────────────────────
BARRIER_FALLBACK = {
    "no_trust": {
        "en": "Fair. Read a few posts in the channel first — no signup, just open it and judge the analysis yourself.",
        "es": "Válido. Leé algunos posts en el canal primero — sin registro, abrí y juzgá el análisis vos mismo.",
    },
    "not_urgent": {
        "en": "No rush. The channel's free and the early reads are time-sensitive — that's the only catch.",
        "es": "Sin apuro. El canal es gratis y las lecturas tempranas son sensibles al tiempo — ese es el único detalle.",
    },
    "thinking": {
        "en": "Take your time. What leagues are you most into? I'll point you to the right reads.",
        "es": "Tomá tu tiempo. ¿Qué ligas te gustan más? Te marco las lecturas correctas.",
    },
}

# ── Фоллбэки ──────────────────────────────────────────────────────────────────
GENERIC_FALLBACK = {
    "en": "📡 Pulling the latest — give me a sec.",
    "es": "📡 Revisando lo último — dame un segundo.",
}

FTD_CONFIRM_PROMPT = {
    "en": "Subscribed? Say yes and I'll point you to today's reads ⚽",
    "es": "¿Te suscribiste? Decí sí y te marco las lecturas de hoy ⚽",
}

MORNING_DIGEST_HEADER = {
    "en": "📅 *Good morning — today's fixtures*\n\n",
    "es": "📅 *Buenos días — los partidos de hoy*\n\n",
}

MORNING_DIGEST_FOOTER = {
    "en": "\n\n⚽ Full reads drop in the channel.",
    "es": "\n\n⚽ Las lecturas completas salen en el canal.",
}

# ── Подписка через бота: нативное сообщение + верификация (рычаг №2) ───────────
# Конверсия через бота выше, чем через кнопку в вебвью: один поток внутри Telegram,
# без контекст-свитча наружу. Тап в мини-аппе → бот шлёт это сообщение с кнопками.
JOIN_PROMPT = {
    "en": (
        "📣 *Join the GoalCast channel — free*\n\n"
        "Full match breakdowns, early reads before kickoff, and results — "
        "all in the channel.\n\n"
        "Tap *Join* below, then hit *✅ I subscribed* and I'll unlock today's full reads. ⚽"
    ),
    "es": (
        "📣 *Unite al canal de GoalCast — gratis*\n\n"
        "Análisis completos, lecturas tempranas antes del pitazo y resultados — "
        "todo en el canal.\n\n"
        "Tocá *Unirme* abajo, luego *✅ Ya me suscribí* y te desbloqueo las lecturas de hoy. ⚽"
    ),
}

JOIN_CHECK_BTN = {"en": "✅ I subscribed", "es": "✅ Ya me suscribí"}

JOIN_OK = {
    "en": (
        "🔓 *Unlocked — you're in*\n\n"
        "Full reads and early picks are yours now. "
        "Keep notifications on so you don't miss the early calls. ⚽"
    ),
    "es": (
        "🔓 *Desbloqueado — estás adentro*\n\n"
        "Las lecturas completas y los picks tempranos ya son tuyos. "
        "Dejá las notificaciones activas para no perderte las primeras. ⚽"
    ),
}

JOIN_NOT_YET = {
    "en": "Hmm — I don't see you in the channel yet. Tap *Join* above, then hit *✅ I subscribed* again. ⚽",
    "es": "Mmm — todavía no te veo en el canal. Tocá *Unirme* arriba y luego *✅ Ya me suscribí* otra vez. ⚽",
}
