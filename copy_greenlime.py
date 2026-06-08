"""
copy_greenlime.py — копирайт бренда Green Lime Feed (деньги/маркеты + live score, режим КАНАЛ)
=============================================================================================
Цель воронки: ПОДПИСКА на Telegram-канал. Не продукт, не ставки.
Персона: зелёный лайм-маскот «Limo» — помешан на том, «куда движутся деньги».
Тон: бодрый, энергичный, money-savvy — репортит цифры и сделки, не хайпит.

⚠️ TELEGRAM ADS COMPLIANCE (строго):
- только НОВОСТИ и ЦИФРЫ; никаких фин/беттинг-советов;
- не зовём покупать/продавать/ставить/депозитить;
- НИКОГДА не обещаем прибыль, доход или выигрыш;
- не рекламируем казино/букмекеров.

Языки: en (дефолт), ru, es. {url} в CTA_REGISTER = ссылка на канал.
"""
from config import CHANNEL_HANDLE

_RAW_HANDLE = CHANNEL_HANDLE or "@your_channel"
CH = _RAW_HANDLE.replace("_", "\\_")

# ── /start HOOK ───────────────────────────────────────────────────────────────
HOOK_CAPTION = {
    "en": (
        "💚 *Green Lime Feed — follow the money*\n\n"
        "I'm Limo 🍋 — I track where the money moves: markets, big deals, prize pools "
        "and live scores, all in one fast feed:\n\n"
        "• 💸 crypto market moves & money news\n"
        "• 🏦 the business side of casino/iGaming, esports & football\n"
        "• 🔴 live scores in real time\n\n"
        "Just the numbers and the headlines — no advice, no promises.\n\n"
        "Which topics should I prioritise for you?"
    ),
    "ru": (
        "💚 *Green Lime Feed — следи за деньгами*\n\n"
        "Я Limo 🍋 — слежу, куда движутся деньги: рынки, крупные сделки, призовые "
        "и live-счёт, всё в одной быстрой ленте:\n\n"
        "• 💸 движения крипторынка и денежные новости\n"
        "• 🏦 деловая сторона казино/iGaming, киберспорта и футбола\n"
        "• 🔴 счёт в реальном времени\n\n"
        "Только цифры и заголовки — без советов и обещаний.\n\n"
        "Какие темы ставить в приоритет?"
    ),
    "es": (
        "💚 *Green Lime Feed — seguí el dinero*\n\n"
        "Soy Limo 🍋 — sigo a dónde se mueve el dinero: mercados, grandes acuerdos, "
        "premios y resultados en vivo, todo en un feed rápido:\n\n"
        "• 💸 movimientos del mercado cripto y noticias de dinero\n"
        "• 🏦 el lado financiero del casino/iGaming, esports y fútbol\n"
        "• 🔴 resultados en vivo en tiempo real\n\n"
        "Solo los números y los titulares — sin consejos ni promesas.\n\n"
        "¿Qué temas priorizo para vos?"
    ),
}

# ── Warmup (новостной/деньги тон, без советов) ────────────────────────────────
WARMUP_FOOTBALL = {
    "en": [
        "💸 The deal that moves a market usually breaks here first.",
        "🔴 Live scores update in real time, no refresh needed.",
        "📊 Markets, deals, prize pools — the money behind the headlines.",
    ],
    "ru": [
        "💸 Сделка, которая двигает рынок, обычно появляется тут первой.",
        "🔴 Live-счёт обновляется в реальном времени, без перезагрузки.",
        "📊 Рынки, сделки, призовые — деньги за заголовками.",
    ],
    "es": [
        "💸 El acuerdo que mueve un mercado suele salir acá primero.",
        "🔴 Los resultados en vivo se actualizan en tiempo real.",
        "📊 Mercados, acuerdos, premios — el dinero detrás de los titulares.",
    ],
}
WARMUP_ESPORTS = WARMUP_FOOTBALL

# ── Bridge ────────────────────────────────────────────────────────────────────
BRIDGE = {
    "en": (
        "🔑 *Where the full money feed lives*\n\n"
        f"The complete feed — instant market alerts and live-score pushes — runs in the "
        f"{CH} channel.\n\n"
        "• 💸 every money move the moment it lands\n"
        "• 🏦 the deals, numbers and transfers in full\n"
        "• 🔴 live-score pings for matches you follow\n\n"
        "It's free, and it's news — not advice. Want the link?"
    ),
    "ru": (
        "🔑 *Где живёт полный денежный фид*\n\n"
        f"Полная лента — мгновенные рыночные алерты и пуши со счётом — идёт в канале {CH}.\n\n"
        "• 💸 каждое движение денег в момент события\n"
        "• 🏦 сделки, цифры и трансферы целиком\n"
        "• 🔴 пинги со счётом по матчам, за которыми следишь\n\n"
        "Бесплатно, и это новости — не советы. Скинуть ссылку?"
    ),
    "es": (
        "🔑 *Dónde vive el feed completo del dinero*\n\n"
        f"El feed completo — alertas de mercado y avisos de resultados — corre en el "
        f"canal {CH}.\n\n"
        "• 💸 cada movimiento de dinero al instante\n"
        "• 🏦 los acuerdos, números y transferencias completos\n"
        "• 🔴 avisos de resultados de los partidos que seguís\n\n"
        "Es gratis, y son noticias — no consejos. ¿Te paso el link?"
    ),
}

# ── CTA ({url} = ссылка на канал) ─────────────────────────────────────────────
CTA_REGISTER = {
    "en": (
        "👇 *Subscribe to the channel — free*\n\n{url}\n\n"
        "Turn on notifications and get every money move and live score the moment it "
        "drops. News only — no advice, no promises. 💚"
    ),
    "ru": (
        "👇 *Подписывайся на канал — бесплатно*\n\n{url}\n\n"
        "Включи уведомления — получай каждое движение денег и счёт в момент события. "
        "Только новости — без советов и обещаний. 💚"
    ),
    "es": (
        "👇 *Suscribite al canal — gratis*\n\n{url}\n\n"
        "Activá notificaciones y recibí cada movimiento de dinero y resultado al "
        "instante. Solo noticias — sin consejos ni promesas. 💚"
    ),
}

# ── Подтверждение подписки ────────────────────────────────────────────────────
FTD_CELEBRATION = {
    "en": "🍋 *You're in*\n\nNotifications on so you don't miss a single market alert or live-score push.",
    "ru": "🍋 *Ты в деле*\n\nУведомления включены — не пропустишь ни одного рыночного алерта и пуша со счётом.",
    "es": "🍋 *Estás adentro*\n\nNotificaciones activadas para no perderte ninguna alerta de mercado ni resultado.",
}

# ── Repeat (в channel-режиме выключено; для совместимости) ────────────────────
REPEAT_PUSH = {
    "en": [
        "💸 Today's biggest money moves are live in the channel.",
        "🔴 Live scores are rolling — check the channel.",
        "📊 Notifications off? That's how you miss the market-movers.",
    ],
    "ru": [
        "💸 Главные денежные движения дня уже в канале.",
        "🔴 Live-счёт идёт — загляни в канал.",
        "📊 Уведомления выключены? Так и теряются рыночные новости.",
    ],
    "es": [
        "💸 Los mayores movimientos de dinero del día están en el canal.",
        "🔴 Los resultados en vivo están corriendo — mirá el canal.",
        "📊 ¿Notificaciones apagadas? Así te perdés las noticias del mercado.",
    ],
}

# ── Возражения ────────────────────────────────────────────────────────────────
BARRIER_FALLBACK = {
    "en": {
        "no_trust": "Fair. Open the channel and read a few posts first — no signup, judge the feed yourself.",
        "not_urgent": "No rush. The channel's free and market alerts are time-sensitive — that's the only catch.",
        "thinking": "Take your time. Which topics are you most into — crypto, casino, esports or football?",
    },
    "ru": {
        "no_trust": "Справедливо. Открой канал и почитай пару постов — без регистрации, оцени ленту сам.",
        "not_urgent": "Без спешки. Канал бесплатный, а рыночные алерты привязаны ко времени — единственный нюанс.",
        "thinking": "Подумай спокойно. Какие темы тебе ближе — крипта, казино, киберспорт или футбол?",
    },
    "es": {
        "no_trust": "Válido. Abrí el canal y leé algunos posts — sin registro, juzgá el feed vos mismo.",
        "not_urgent": "Sin apuro. El canal es gratis y las alertas dependen del tiempo — ese es el único detalle.",
        "thinking": "Tomate tu tiempo. ¿Qué temas te interesan más — cripto, casino, esports o fútbol?",
    },
}

# ── Фоллбэки ──────────────────────────────────────────────────────────────────
GENERIC_FALLBACK = {
    "en": "💚 Pulling the latest money moves — one sec.",
    "ru": "💚 Подтягиваю свежие движения по деньгам — секунду.",
    "es": "💚 Buscando los últimos movimientos de dinero — un segundo.",
}

FTD_CONFIRM_PROMPT = {
    "en": "Subscribed? Say yes and I'll point you to today's biggest money moves.",
    "ru": "Подписался? Скажи «да» — и подскажу главные денежные движения дня.",
    "es": "¿Te suscribiste? Decí sí y te marco los mayores movimientos de dinero de hoy.",
}

MORNING_DIGEST_HEADER = {
    "en": "📅 *Good morning — today's fixtures*\n\n",
    "ru": "📅 *Доброе утро — матчи на сегодня*\n\n",
    "es": "📅 *Buen día — los partidos de hoy*\n\n",
}

MORNING_DIGEST_FOOTER = {
    "en": f"\n\n💚 Live-score pushes + full money feed — in the channel {CH}.",
    "ru": f"\n\n💚 Пуши со счётом + полный денежный фид — в канале {CH}.",
    "es": f"\n\n💚 Avisos de resultados + feed completo de dinero — en el canal {CH}.",
}

# ── Нативное приглашение в канал + верификация ────────────────────────────────
JOIN_PROMPT = {
    "en": (
        "💚 *Subscribe to the channel*\n\nFull money feed, market alerts and live-score "
        "pushes — free. Tap subscribe, then come back and check access. 👇"
    ),
    "ru": (
        "💚 *Подписывайся на канал*\n\nПолный денежный фид, рыночные алерты и пуши со "
        "счётом — бесплатно. Нажми «Подписаться», затем вернись и проверь доступ. 👇"
    ),
    "es": (
        "💚 *Suscribite al canal*\n\nFeed completo de dinero, alertas de mercado y avisos "
        "de resultados — gratis. Tocá suscribirte, después volvé y verificá el acceso. 👇"
    ),
}
JOIN_CHECK_BTN = {"en": "✅ I subscribed", "ru": "✅ Я подписался", "es": "✅ Ya me suscribí"}
JOIN_OK = {
    "en": "✅ Done — access unlocked. The full money feed is live in the channel.",
    "ru": "✅ Готово — доступ открыт. Полный денежный фид уже в канале.",
    "es": "✅ Listo — acceso desbloqueado. El feed completo del dinero está en el canal.",
}
JOIN_NOT_YET = {
    "en": "🔒 Don't see your subscription yet. Join the channel and tap “I subscribed” again.",
    "ru": "🔒 Пока не вижу подписки. Подпишись на канал и нажми «Я подписался» ещё раз.",
    "es": "🔒 Todavía no veo tu suscripción. Unite al canal y tocá «Ya me suscribí» de nuevo.",
}

# ══════════════════════════════════════════════════════════════════════════════
#  NEWS-специфичный копирайт (лента в боте)
# ══════════════════════════════════════════════════════════════════════════════
NEWS_HEADER = {
    "en": "💸 *Latest — Green Lime Feed*\n\n",
    "ru": "💸 *Свежее — Green Lime Feed*\n\n",
    "es": "💸 *Lo último — Green Lime Feed*\n\n",
}
NEWS_EMPTY = {
    "en": "💚 Feed is warming up — try again in a moment.",
    "ru": "💚 Лента прогревается — попробуй ещё раз через минуту.",
    "es": "💚 El feed se está calentando — probá de nuevo en un momento.",
}
# Дописывается в конец ленты ТОЛЬКО неподписчикам (рычаг конверсии).
NEWS_FOOTER = {
    "en": f"\n\n💚 *This is the preview.* The full money feed + instant market alerts run in the channel {CH}.",
    "ru": f"\n\n💚 *Это превью.* Полный денежный фид + мгновенные рыночные алерты идут в канале {CH}.",
    "es": f"\n\n💚 *Esto es la vista previa.* El feed completo + alertas de mercado corren en el canal {CH}.",
}
# Подписи инлайн-кнопок переключения категорий.
NEWS_CAT_LABELS = {
    "en": {"all": "🌐 All", "crypto": "₿ Crypto", "casino": "🎰 Casino", "esports": "🎮 Esports"},
    "ru": {"all": "🌐 Все", "crypto": "₿ Крипто", "casino": "🎰 Казино", "esports": "🎮 Киберспорт"},
    "es": {"all": "🌐 Todo", "crypto": "₿ Cripto", "casino": "🎰 Casino", "esports": "🎮 Esports"},
}
# Строка-нудж под live-счётом для неподписчиков.
LIVE_CHANNEL_LINE = {
    "en": f"\n\n💚 _Live-score pushes for these — in the channel {CH}._",
    "ru": f"\n\n💚 _Пуши со счётом по этим матчам — в канале {CH}._",
    "es": f"\n\n💚 _Avisos de resultados de estos — en el canal {CH}._",
}
