"""
messages.py — MetaPlay by Coinplay
Persona: Mateo — esports & football analyst. Knows the game, shares his edge.
Languages: EN (Vietnam/India), ES-LATAM (Peru/Colombia/Argentina)
Tone: insider, sharp, genuine — not a promoter, an analyst who shares his reads.

Ad copy angle: "Know the game before it happens."
Clean for Telegram Ads + App Store / Google Play moderation.
"""

# ── /start HOOK ───────────────────────────────────────────────────────────────
HOOK_CAPTION = {
    "en": (
        "📡 *MetaPlay — read the game before it starts*\n\n"
        "I'm Mateo. Full-time esports & football analyst — "
        "CS2, Dota, LoL, football, all of it.\n\n"
        "Every day I share:\n"
        "• Live scores & real-time match updates\n"
        "• AI pre-match analysis with full reasoning\n"
        "• Early signals before key matches kick off\n\n"
        "Quick question — ⚽ Football or 🎮 Esports?"
    ),
    "es": (
        "📡 *MetaPlay — leé el partido antes de que empiece*\n\n"
        "Soy Mateo. Analista de esports y fútbol a tiempo completo — "
        "CS2, Dota, LoL, fútbol, todo.\n\n"
        "Cada día comparto:\n"
        "• Resultados en vivo y actualizaciones en tiempo real\n"
        "• Análisis pre-partido con razonamiento completo\n"
        "• Señales tempranas antes de los partidos clave\n\n"
        "Una pregunta rápida — ⚽ Fútbol o 🎮 Esports?"
    ),
}

# ── Warmup responses (before bridge) ─────────────────────────────────────────
WARMUP_ESPORTS = {
    "en": [
        "🎮 Esports is where the real edge hides. "
        "CS2 and Dota markets move fast before matches — "
        "form, meta shifts, roster changes. "
        "Knowing this beforehand separates sharp analysis from noise.",

        "📊 CS2 Major qualifiers are a goldmine for analysis. "
        "Top seeds get complacent, underdogs are constantly underrated. "
        "Tracking this before matches start is where the real reads come from.",

        "⚡ The meta in LoL this patch has flipped — "
        "jungle-dominant teams are winning 60%+ of games right now. "
        "That's the kind of signal most analysts miss entirely.",
    ],
    "es": [
        "🎮 Los esports son donde se esconde el verdadero análisis. "
        "Los mercados de CS2 y Dota se mueven rápido antes de los partidos — "
        "forma, cambios de meta, bajas. "
        "Conocer esto de antemano separa el análisis serio del ruido.",

        "📊 Los qualifiers de CS2 Major son una mina de información. "
        "Las cabezas de serie se confían, los underdogs siempre están subestimados. "
        "Seguir esto antes de los partidos es donde están las mejores lecturas.",

        "⚡ El meta de LoL este parche cambió todo — "
        "los equipos con dominio de jungla están ganando más del 60% ahora mismo. "
        "Es el tipo de señal que la mayoría de analistas nunca ve.",
    ],
}

WARMUP_FOOTBALL = {
    "en": [
        "⚽ Football is where I started. Libertadores and Latam leagues "
        "are massively underanalyzed compared to European markets — "
        "that's where the sharpest reads come from every week.",

        "📊 Libertadores group stage is where coverage is thinnest. "
        "Home/away splits in South American football are dramatic "
        "and almost nobody is tracking them properly.",

        "💡 Most people follow teams they support. "
        "I follow data — form, head-to-head, travel fatigue, lineup changes. "
        "That's what makes the analysis consistent.",
    ],
    "es": [
        "⚽ El fútbol fue por donde empecé. La Libertadores y las ligas latinoamericanas "
        "están masivamente subanalizada vs. los mercados europeos — "
        "ahí están las lecturas más interesantes cada semana.",

        "📊 La fase de grupos de Libertadores es donde el análisis es más escaso. "
        "Las diferencias local/visitante en el fútbol sudamericano son enormes "
        "y casi nadie las rastrea como corresponde.",

        "💡 La mayoría sigue al equipo que le gusta. "
        "Yo sigo datos — forma, head-to-head, cansancio de viaje, formaciones. "
        "Por eso el análisis es consistente.",
    ],
}

# ── Bridge: introducing Coinplay ──────────────────────────────────────────────
BRIDGE = {
    "en": (
        "🔑 *Where I place my analysis into action*\n\n"
        "I use Coinplay — crypto sportsbook covering esports, football, everything.\n\n"
        "Why specifically:\n"
        "• Instant crypto transactions (BTC, ETH, USDT, 40+ coins)\n"
        "• No bank account needed\n"
        "• Deepest esports coverage — CS2, LoL, Dota, Valorant\n"
        "• Right now: *100% bonus up to $5,000 USDT + 80 free spins* on first deposit\n\n"
        "Minimum is 20 USDT.\n\n"
        "Want me to send you the link?"
    ),
    "es": (
        "🔑 *Donde pongo mi análisis en acción*\n\n"
        "Uso Coinplay — sportsbook cripto que cubre esports, fútbol, todo.\n\n"
        "Por qué específicamente:\n"
        "• Transacciones cripto instantáneas (BTC, ETH, USDT, 40+ monedas)\n"
        "• Sin cuenta bancaria\n"
        "• La cobertura de esports más profunda — CS2, LoL, Dota, Valorant\n"
        "• Ahora mismo: *100% de bono hasta $5,000 USDT + 80 giros gratis* en el primer depósito\n\n"
        "Mínimo 20 USDT.\n\n"
        "¿Te mando el link?"
    ),
}

# ── CTA ───────────────────────────────────────────────────────────────────────
CTA_REGISTER = {
    "en": (
        "👇 *Join Coinplay — takes 2 minutes*\n\n"
        "{url}\n\n"
        "Deposit any crypto (20 USDT minimum). "
        "The 100% bonus + 80 free spins activates automatically.\n\n"
        "Message me once you're in — I'll drop today's full analysis right away 🎯"
    ),
    "es": (
        "👇 *Unite a Coinplay — 2 minutos*\n\n"
        "{url}\n\n"
        "Depositá cualquier cripto (mínimo 20 USDT). "
        "El bono 100% + 80 giros gratis se activa automáticamente.\n\n"
        "Escribime cuando estés adentro — te mando el análisis completo de hoy de inmediato 🎯"
    ),
}

# ── FTD celebration ───────────────────────────────────────────────────────────
FTD_CELEBRATION = {
    "en": (
        "🔥 *You're in — let's go*\n\n"
        "Start small, get familiar with the platform.\n\n"
        "The 5% weekly cashback means even quiet stretches cost less than you think.\n\n"
        "I'll send analysis every day. When I'm confident in a call — I'll be clear about it. 📡"
    ),
    "es": (
        "🔥 *Estás adentro — vamos*\n\n"
        "Empezá pequeño, conocé la plataforma.\n\n"
        "El cashback semanal del 5% significa que hasta las rachas tranquilas cuestan menos de lo que pensás.\n\n"
        "Mando análisis todos los días. Cuando estoy seguro de algo — lo digo claramente. 📡"
    ),
}

# ── Repeat deposit pushes ─────────────────────────────────────────────────────
REPEAT_PUSH = {
    "en": [
        "⚡ Match starting in 30 minutes — one I've been tracking all week. "
        "Let me know if you want the full breakdown before it starts.",

        "📊 Evening wrap — 3 results today, 2 went my way. "
        "If your balance is low, a small top-up puts you back in the mix for tomorrow.",

        "📡 Checking in — how's the platform feeling? "
        "If you haven't used the free spins yet, they have an expiry. "
        "That's free value just sitting there.",

        "🎮 Big esports weekend — PGL and LCK have standout matchups. "
        "I'm going in heavier than usual. Top up if you want in on this.",

        "🔑 Weekly recap — picks went 5/7 this week. "
        "Next up: Libertadores and LEC playoffs. "
        "Active Coinplay users get the full breakdown first.",
    ],
    "es": [
        "⚡ Partido en 30 minutos — uno que vengo siguiendo toda la semana. "
        "Avisame si querés el análisis completo antes de que empiece.",

        "📊 Resumen nocturno — 3 resultados hoy, 2 me salieron bien. "
        "Si tu saldo está bajo, un pequeño recargo te vuelve a meter en la acción de mañana.",

        "📡 Te escribo — ¿cómo va la plataforma? "
        "Si todavía no usaste los giros gratis, tienen vencimiento. "
        "Es valor gratis que ya tenés ahí.",

        "🎮 Gran fin de semana de esports — PGL y LCK tienen partidos destacados. "
        "Voy a entrar más fuerte de lo normal. Recargá si querés estar en esto.",

        "🔑 Resumen semanal — picks fueron 5/7 esta semana. "
        "Lo que viene: Libertadores y playoffs de LEC. "
        "Los usuarios activos en Coinplay reciben el análisis completo primero.",
    ],
}

# ── Barrier fallbacks ─────────────────────────────────────────────────────────
BARRIER_FALLBACK = {
    "no_money": {
        "en": "20 USDT is the minimum — that's around $20. "
              "Even just registering now locks in the 100% bonus for when you're ready.",
        "es": "El mínimo son 20 USDT — unos $20. "
              "Aunque solo te registres ahora, el bono del 100% queda asegurado para cuando estés listo.",
    },
    "no_trust": {
        "en": "Fair point — Coinplay runs on a Curacao license, operating since 2022. "
              "All transactions are on-chain verifiable. I've withdrawn multiple times without issues.",
        "es": "Válido — Coinplay opera con licencia de Curacao desde 2022. "
              "Todas las transacciones son verificables on-chain. Retiré múltiples veces sin problemas.",
    },
    "dont_understand": {
        "en": "It's straightforward: deposit crypto → follow the analysis I send → "
              "withdraw back to your wallet. No bank needed. What part is unclear?",
        "es": "Es simple: depositás cripto → seguís el análisis que te mando → "
              "retirás a tu billetera. Sin banco. ¿Qué parte no quedó clara?",
    },
    "not_urgent": {
        "en": "No pressure. The 100% bonus is a promo though — it won't be there forever.",
        "es": "Sin apuro. Aunque el bono del 100% es una promo — no dura para siempre.",
    },
    "already_elsewhere": {
        "en": "Where are you now? Two things worth checking: "
              "esports market depth and withdrawal speed. "
              "Most platforms are thin on CS2/Dota lines compared to Coinplay.",
        "es": "¿Dónde estás ahora? Dos cosas que vale la pena revisar: "
              "profundidad de mercado en esports y velocidad de retiro. "
              "La mayoría es escasa en líneas de CS2/Dota vs Coinplay.",
    },
    "thinking": {
        "en": "Take your time. What's the main thing holding you back?",
        "es": "Tomá tu tiempo. ¿Qué es lo principal que te frena?",
    },
}

# ── Generic fallback ──────────────────────────────────────────────────────────
GENERIC_FALLBACK = {
    "en": "📡 Pulling the latest data — give me a sec.",
    "es": "📡 Revisando los últimos datos — dame un segundo.",
}

FTD_CONFIRM_PROMPT = {
    "en": "Did you make your first deposit? Reply yes and I'll send today's full analysis right away 🎯",
    "es": "¿Hiciste tu primer depósito? Decí sí y te mando el análisis completo de hoy de inmediato 🎯",
}

MORNING_DIGEST_HEADER = {
    "en": "📅 *Good morning — here's today's slate*\n\n",
    "es": "📅 *Buenos días — acá está el programa de hoy*\n\n",
}

MORNING_DIGEST_FOOTER = {
    "en": "\n\n🎯 My picks drop at noon. Stay sharp.",
    "es": "\n\n🎯 Mis picks llegan al mediodía. Mantenete atento.",
}

# ── Подписка на канал: заглушки для совместимости ─────────────────────────────
# metaplay ведёт в продукт (channel-флоу не используется), но messages.py
# реэкспортит имена для ВСЕХ брендов — поэтому ключи должны существовать и здесь.
JOIN_PROMPT = {
    "en": (
        "📣 *Join the channel — free*\n\n"
        "Tap *Join* below, then hit *✅ I subscribed* to unlock the full reads."
    ),
    "es": (
        "📣 *Unite al canal — gratis*\n\n"
        "Tocá *Unirme* abajo y luego *✅ Ya me suscribí* para desbloquear las lecturas."
    ),
}

JOIN_CHECK_BTN = {"en": "✅ I subscribed", "es": "✅ Ya me suscribí"}

JOIN_OK = {
    "en": "🔓 *Unlocked — you're in.* Full reads are yours now.",
    "es": "🔓 *Desbloqueado — estás adentro.* Las lecturas completas ya son tuyas.",
}

JOIN_NOT_YET = {
    "en": "Hmm — I don't see you in the channel yet. Tap *Join* above, then *✅ I subscribed* again.",
    "es": "Mmm — todavía no te veo en el canal. Tocá *Unirme* arriba y luego *✅ Ya me suscribí* otra vez.",
}
