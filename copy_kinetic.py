"""
copy_kinetic.py — копирайт бренда Kinetic Feed (новости + live score, режим КАНАЛ)
=========================================================================
Цель воронки: ПОДПИСКА на Telegram-канал. Не продукт, не ставки.
Тон: нейтральный новостной/score-ведущий (Kit) — репортит, не хайпит,
зовёт в канал за полным фидом и мгновенными алертами.

Политика: НЕ рекламируем казино/букмекеров, не зовём ставить/депозитить,
не обещаем выигрыши, без дутой статистики и фейковых «подписчиков».

Языки: en (приоритет/дефолт), ru, es. Неизвестный язык → en
(через .get(lang, X["en"]) на стороне вызова). {url} в CTA_REGISTER = ссылка на канал.
"""
from config import CHANNEL_HANDLE

# Хэндл для отображения в Markdown. Подчёркивание в @handle ломает MarkdownV1,
# поэтому экранируем '_'. В мини-апп (через /api/config) уходит сырой handle.
_RAW_HANDLE = CHANNEL_HANDLE or "@your_channel"
CH = _RAW_HANDLE.replace("_", "\\_")

# ── /start HOOK ───────────────────────────────────────────────────────────────
HOOK_CAPTION = {
    "en": (
        "📡 *Kinetic Feed — news & live scores, the moment they break*\n\n"
        "I'm Kit. I track crypto, casino-industry, esports & football and turn it "
        "into one fast feed:\n\n"
        "• 📰 breaking headlines across all four\n"
        "• 🔴 live scores in real time\n"
        "• 📣 instant alerts before everyone else\n\n"
        "Which topics do you want me to prioritise?"
    ),
    "ru": (
        "📡 *Kinetic Feed — новости и live-счёт в момент события*\n\n"
        "Я Kit. Веду крипту, индустрию казино, киберспорт и футбол — собираю всё "
        "в одну быструю ленту:\n\n"
        "• 📰 свежие заголовки по всем четырём темам\n"
        "• 🔴 счёт в реальном времени\n"
        "• 📣 мгновенные алерты раньше всех\n\n"
        "Какие темы тебе важнее всего?"
    ),
    "es": (
        "📡 *Kinetic Feed — noticias y resultados en vivo, al instante*\n\n"
        "Soy Kit. Sigo cripto, la industria del casino, esports y fútbol y lo "
        "convierto en un feed rápido:\n\n"
        "• 📰 titulares de última hora en los cuatro temas\n"
        "• 🔴 resultados en vivo en tiempo real\n"
        "• 📣 alertas instantáneas antes que nadie\n\n"
        "¿Qué temas querés que priorice?"
    ),
}

# ── Warmup (короткие реплики-наполнители; новостной тон) ──────────────────────
WARMUP_FOOTBALL = {
    "en": [
        "📡 The story that moves a market usually breaks here first — then everyone else.",
        "🔴 Live scores update in real time, no refresh needed.",
        "📰 Crypto, casino, esports, football — one feed, zero noise.",
    ],
    "ru": [
        "📡 Новость, которая двигает рынок, обычно появляется тут первой — а потом у всех.",
        "🔴 Live-счёт обновляется в реальном времени, без перезагрузки.",
        "📰 Крипта, казино, киберспорт, футбол — одна лента, ноль шума.",
    ],
    "es": [
        "📡 La noticia que mueve un mercado suele salir acá primero — después en el resto.",
        "🔴 Los resultados en vivo se actualizan en tiempo real, sin recargar.",
        "📰 Cripto, casino, esports, fútbol — un solo feed, cero ruido.",
    ],
}
WARMUP_ESPORTS = WARMUP_FOOTBALL

# ── Bridge ────────────────────────────────────────────────────────────────────
BRIDGE = {
    "en": (
        "🔑 *Where the full feed lives*\n\n"
        f"The complete feed — instant breaking alerts and live-score pushes — runs in "
        f"the {CH} channel.\n\n"
        "• 📰 every headline the moment it lands\n"
        "• 🔴 live-score pings for matches you follow\n"
        "• 📣 first alerts before the crowd\n\n"
        "It's free. Want the link?"
    ),
    "ru": (
        "🔑 *Где живёт полный фид*\n\n"
        f"Полная лента — мгновенные алерты и пуши со счётом — идёт в канале {CH}.\n\n"
        "• 📰 каждый заголовок в момент выхода\n"
        "• 🔴 пинги со счётом по матчам, за которыми следишь\n"
        "• 📣 первые алерты раньше толпы\n\n"
        "Вход бесплатный. Скинуть ссылку?"
    ),
    "es": (
        "🔑 *Dónde vive el feed completo*\n\n"
        f"El feed completo — alertas instantáneas y avisos de resultados — corre en el "
        f"canal {CH}.\n\n"
        "• 📰 cada titular al instante\n"
        "• 🔴 avisos de resultados de los partidos que seguís\n"
        "• 📣 primeras alertas antes que el resto\n\n"
        "Es gratis. ¿Te paso el link?"
    ),
}

# ── CTA ({url} = ссылка на канал) ─────────────────────────────────────────────
CTA_REGISTER = {
    "en": (
        "👇 *Subscribe to the channel — free*\n\n{url}\n\n"
        "Tap subscribe, turn on notifications, and get every headline and live score "
        "the moment it drops. 📡"
    ),
    "ru": (
        "👇 *Подписывайся на канал — бесплатно*\n\n{url}\n\n"
        "Нажми «Подписаться», включи уведомления — получай каждый заголовок и счёт "
        "в момент события. 📡"
    ),
    "es": (
        "👇 *Suscribite al canal — gratis*\n\n{url}\n\n"
        "Tocá suscribirte, activá notificaciones y recibí cada titular y resultado "
        "al instante. 📡"
    ),
}

# ── Подтверждение подписки (переиспользуется как «ты в деле») ──────────────────
FTD_CELEBRATION = {
    "en": (
        "🔥 *You're in*\n\nNotifications on so you don't miss a single breaking alert "
        "or live-score push."
    ),
    "ru": (
        "🔥 *Ты в деле*\n\nУведомления включены — не пропустишь ни одного алерта "
        "и пуша со счётом."
    ),
    "es": (
        "🔥 *Estás adentro*\n\nNotificaciones activadas para no perderte ninguna alerta "
        "ni aviso de resultado."
    ),
}

# ── Repeat (в channel-режиме выключено; оставлено для совместимости) ──────────
REPEAT_PUSH = {
    "en": [
        "📰 Today's top stories are live in the channel.",
        "🔴 Live scores are rolling — check the channel.",
        "📣 Notifications off? That's how you miss the breaking ones.",
    ],
    "ru": [
        "📰 Главные новости дня уже в канале.",
        "🔴 Live-счёт идёт — загляни в канал.",
        "📣 Уведомления выключены? Так и теряются срочные новости.",
    ],
    "es": [
        "📰 Las noticias top del día están en el canal.",
        "🔴 Los resultados en vivo están corriendo — mirá el canal.",
        "📣 ¿Notificaciones apagadas? Así te perdés las de última hora.",
    ],
}

# ── Возражения ────────────────────────────────────────────────────────────────
BARRIER_FALLBACK = {
    "en": {
        "no_trust": "Fair. Open the channel and read a few posts first — no signup, judge the feed yourself.",
        "not_urgent": "No rush. The channel's free and breaking alerts are time-sensitive — that's the only catch.",
        "thinking": "Take your time. Which topics are you most into — crypto, casino, esports or football?",
    },
    "ru": {
        "no_trust": "Справедливо. Открой канал и почитай пару постов — без регистрации, оцени ленту сам.",
        "not_urgent": "Без спешки. Канал бесплатный, а срочные алерты привязаны ко времени — единственный нюанс.",
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
    "en": "📡 Pulling the latest — one sec.",
    "ru": "📡 Подтягиваю свежее — секунду.",
    "es": "📡 Buscando lo último — un segundo.",
}

FTD_CONFIRM_PROMPT = {
    "en": "Subscribed? Say yes and I'll point you to today's top stories.",
    "ru": "Подписался? Скажи «да» — и подскажу главные новости дня.",
    "es": "¿Te suscribiste? Decí sí y te marco las noticias top de hoy.",
}

MORNING_DIGEST_HEADER = {
    "en": "📅 *Good morning — today's fixtures*\n\n",
    "ru": "📅 *Доброе утро — матчи на сегодня*\n\n",
    "es": "📅 *Buen día — los partidos de hoy*\n\n",
}

MORNING_DIGEST_FOOTER = {
    "en": f"\n\n📣 Live-score pushes + full feed — in the channel {CH}.",
    "ru": f"\n\n📣 Пуши со счётом + полный фид — в канале {CH}.",
    "es": f"\n\n📣 Avisos de resultados + feed completo — en el canal {CH}.",
}

# ── Нативное приглашение в канал + верификация ────────────────────────────────
JOIN_PROMPT = {
    "en": (
        "📣 *Subscribe to the channel*\n\nFull feed, breaking alerts and live-score "
        "pushes — free. Tap subscribe, then come back and check access. 👇"
    ),
    "ru": (
        "📣 *Подписывайся на канал*\n\nПолный фид, срочные алерты и пуши со счётом — "
        "бесплатно. Нажми «Подписаться», затем вернись и проверь доступ. 👇"
    ),
    "es": (
        "📣 *Suscribite al canal*\n\nFeed completo, alertas de última hora y avisos de "
        "resultados — gratis. Tocá suscribirte, después volvé y verificá el acceso. 👇"
    ),
}
JOIN_CHECK_BTN = {"en": "✅ I subscribed", "ru": "✅ Я подписался", "es": "✅ Ya me suscribí"}
JOIN_OK = {
    "en": "✅ Done — access unlocked. The full feed is live in the channel.",
    "ru": "✅ Готово — доступ открыт. Полный фид уже в канале.",
    "es": "✅ Listo — acceso desbloqueado. El feed completo está en el canal.",
}
JOIN_NOT_YET = {
    "en": "🔒 Don't see your subscription yet. Join the channel and tap “I subscribed” again.",
    "ru": "🔒 Пока не вижу подписки. Подпишись на канал и нажми «Я подписался» ещё раз.",
    "es": "🔒 Todavía no veo tu suscripción. Unite al canal y tocá «Ya me suscribí» de nuevo.",
}

# ══════════════════════════════════════════════════════════════════════════════
#  NEWS-специфичный копирайт (новый — для ленты в боте)
# ══════════════════════════════════════════════════════════════════════════════
NEWS_HEADER = {
    "en": "📰 *Latest — Kinetic Feed*\n\n",
    "ru": "📰 *Свежее — лента Kinetic Feed*\n\n",
    "es": "📰 *Lo último — feed de Kinetic Feed*\n\n",
}
NEWS_EMPTY = {
    "en": "📡 Feed is warming up — try again in a moment.",
    "ru": "📡 Лента прогревается — попробуй ещё раз через минуту.",
    "es": "📡 El feed se está calentando — probá de nuevo en un momento.",
}
# Дописывается в конец ленты ТОЛЬКО неподписчикам (рычаг конверсии).
NEWS_FOOTER = {
    "en": f"\n\n📣 *This is the preview.* The full feed + instant breaking alerts run in the channel {CH}.",
    "ru": f"\n\n📣 *Это превью.* Полный фид + мгновенные алерты идут в канале {CH}.",
    "es": f"\n\n📣 *Esto es la vista previa.* El feed completo + alertas instantáneas corren en el canal {CH}.",
}
# Подписи инлайн-кнопок переключения категорий.
NEWS_CAT_LABELS = {
    "en": {"all": "🌐 All", "crypto": "₿ Crypto", "casino": "🎰 Casino", "esports": "🎮 Esports"},
    "ru": {"all": "🌐 Все", "crypto": "₿ Крипто", "casino": "🎰 Казино", "esports": "🎮 Киберспорт"},
    "es": {"all": "🌐 Todo", "crypto": "₿ Cripto", "casino": "🎰 Casino", "esports": "🎮 Esports"},
}
# Строка-нудж под live-счётом для неподписчиков.
LIVE_CHANNEL_LINE = {
    "en": f"\n\n📣 _Live-score pushes for these — in the channel {CH}._",
    "ru": f"\n\n📣 _Пуши со счётом по этим матчам — в канале {CH}._",
    "es": f"\n\n📣 _Avisos de resultados de estos — en el canal {CH}._",
}
