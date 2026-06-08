"""
copy_metaplay_channel.py — копирайт бренда MetaPlay (режим КАНАЛ)
=================================================================
Цель воронки: ПОДПИСКА на Telegram-канал (не продукт, не ставки).
Тон: аналитик делится разбором и зовёт в канал за полными разборами.

Политика: НЕ рекламируем казино/букмекеров, не зовём ставить/депозитить,
не обещаем выигрыши, без дутой статистики и фейковых «подписчиков».

Языки: en (приоритет/дефолт), ru, es. Любой неизвестный язык → en
(через .get(lang, X["en"]) на стороне вызова).
{url} в CTA_REGISTER = ссылка на канал.
"""
from config import CHANNEL_HANDLE

# Хэндл для отображения в Markdown-сообщениях бота. Подчёркивание в @handle —
# это курсив в MarkdownV1 и ломает парсинг ("Can't parse entities"), поэтому
# экранируем '_'. В мини-апп (через /api/config) уходит сырой handle, без экранов.
_RAW_HANDLE = CHANNEL_HANDLE or "@your_channel"
CH = _RAW_HANDLE.replace("_", "\\_")

# ── /start HOOK ───────────────────────────────────────────────────────────────
HOOK_CAPTION = {
    "en": (
        "📡 *MetaPlay — read the game before kickoff*\n\n"
        "I'm Mateo, an esports & football analyst. Form, head-to-head, maps, "
        "lineups — I track it all and turn it into one clear read.\n\n"
        "Every day I post:\n"
        "• live scores in real time\n"
        "• pre-match breakdowns with the reasoning\n"
        "• early signals before the start\n\n"
        "Which games or leagues do you follow?"
    ),
    "ru": (
        "📡 *MetaPlay — читаем игру до начала матча*\n\n"
        "Я Mateo, аналитик по киберспорту и футболу. Форма, очные встречи, карты, "
        "составы — собираю всё в один разбор.\n\n"
        "Каждый день выкладываю:\n"
        "• счёт в реальном времени\n"
        "• предматчевые разборы с логикой\n"
        "• ранние сигналы до старта\n\n"
        "За какими дисциплинами или лигами следишь?"
    ),
    "es": (
        "📡 *MetaPlay — leé el partido antes del pitazo*\n\n"
        "Soy Mateo, analista de esports y fútbol. Forma, head-to-head, mapas, "
        "alineaciones — sigo todo y lo convierto en una lectura clara.\n\n"
        "Cada día publico:\n"
        "• resultados en vivo\n"
        "• análisis pre-partido con el razonamiento\n"
        "• señales tempranas antes del inicio\n\n"
        "¿Qué juegos o ligas seguís?"
    ),
}

# ── Warmup ────────────────────────────────────────────────────────────────────
WARMUP_FOOTBALL = {
    "en": [
        "📊 Most people back the team they love. I follow the data — form, "
        "head-to-head, fixture congestion. That's where the edge is.",
        "💡 Midweek European nights wreck weekend form. Fatigue is the most "
        "underrated factor in football.",
        "🎯 Home/away splits swing matches more than the table suggests. "
        "Tracking them properly is half the read.",
    ],
    "ru": [
        "📊 Большинство болеет за любимую команду. Я смотрю на данные — форму, "
        "очные встречи, плотность календаря. Там и есть преимущество.",
        "💡 Еврокубковые матчи в середине недели ломают форму на выходных — "
        "самый недооценённый фактор.",
        "🎯 Домашние и гостевые отрезки решают чаще, чем кажется по таблице. "
        "Отслеживать их — половина разбора.",
    ],
    "es": [
        "📊 La mayoría apoya al equipo que ama. Yo sigo los datos — forma, "
        "head-to-head, congestión de partidos. Ahí está la ventaja.",
        "💡 Las noches europeas de entresemana destruyen la forma del finde. "
        "El cansancio es el factor más subestimado.",
        "🎯 Los splits local/visitante mueven partidos más de lo que dice la tabla. "
        "Rastrearlos bien es la mitad de la lectura.",
    ],
}
WARMUP_ESPORTS = WARMUP_FOOTBALL

# ── Bridge ────────────────────────────────────────────────────────────────────
BRIDGE = {
    "en": (
        "🔑 *Where the full reads live*\n\n"
        f"I post the deep match breakdowns in the {CH} channel — the ones that "
        "don't fit here.\n\n"
        "• daily pre-match analysis\n"
        "• early signals before kickoff\n"
        "• results and what I got wrong\n\n"
        "It's free. Want the link?"
    ),
    "ru": (
        "🔑 *Где лежат полные разборы*\n\n"
        f"Глубокие разборы матчей публикую в канале {CH} — те, что не помещаются сюда.\n\n"
        "• ежедневные предматчевые разборы\n"
        "• ранние сигналы до старта\n"
        "• итоги и работа над ошибками\n\n"
        "Вход бесплатный. Скинуть ссылку?"
    ),
    "es": (
        "🔑 *Dónde viven las lecturas completas*\n\n"
        f"Los análisis profundos los publico en el canal {CH} — los que no entran acá.\n\n"
        "• análisis pre-partido diario\n"
        "• señales tempranas antes del inicio\n"
        "• resultados y en qué me equivoqué\n\n"
        "Es gratis. ¿Te paso el link?"
    ),
}

# ── CTA ({url} = ссылка на канал) ─────────────────────────────────────────────
CTA_REGISTER = {
    "en": (
        "👇 *Subscribe to the channel — free*\n\n{url}\n\n"
        "Tap subscribe, turn on notifications, and get every read the moment it drops. ⚽🎮"
    ),
    "ru": (
        "👇 *Подписывайся на канал — бесплатно*\n\n{url}\n\n"
        "Нажми «Подписаться», включи уведомления — получай каждый разбор в момент выхода. ⚽🎮"
    ),
    "es": (
        "👇 *Suscribite al canal — gratis*\n\n{url}\n\n"
        "Tocá suscribirte, activá notificaciones y recibí cada lectura al instante. ⚽🎮"
    ),
}

# ── Подтверждение подписки ────────────────────────────────────────────────────
FTD_CELEBRATION = {
    "en": (
        "🔥 *You're in*\n\nNotifications on so you don't miss the early signals. "
        "I post the day's slate every morning."
    ),
    "ru": (
        "🔥 *Ты в деле*\n\nУведомления включены — не пропустишь ранние сигналы. "
        "Программу дня выкладываю каждое утро."
    ),
    "es": (
        "🔥 *Estás adentro*\n\nNotificaciones activadas para no perderte las señales tempranas. "
        "Publico el programa del día cada mañana."
    ),
}

# ── Repeat (в channel-режиме выключено) ───────────────────────────────────────
REPEAT_PUSH = {
    "en": [
        "⚽ Today's slate is up in the channel — check the early signals.",
        "📊 Post-match notes are live. Worth a look before tomorrow.",
        "📣 Haven't turned on notifications? That's how you miss the early reads.",
    ],
    "ru": [
        "⚽ Программа на сегодня уже в канале — глянь ранние сигналы.",
        "📊 Итоги матчей опубликованы. Стоит заглянуть перед завтрашним днём.",
        "📣 Не включил уведомления? Так и теряются ранние сигналы.",
    ],
    "es": [
        "⚽ El programa de hoy está en el canal — mirá las señales tempranas.",
        "📊 Las notas post-partido ya están. Vale la pena antes de mañana.",
        "📣 ¿No activaste notificaciones? Así te perdés las lecturas tempranas.",
    ],
}

# ── Возражения ────────────────────────────────────────────────────────────────
BARRIER_FALLBACK = {
    "en": {
        "no_trust": "Fair. Read a few posts in the channel first — no signup, just open it and judge the analysis yourself.",
        "not_urgent": "No rush. The channel's free and the early signals are time-sensitive — that's the only catch.",
        "thinking": "Take your time. Which leagues are you most into? I'll point you to the right reads.",
    },
    "ru": {
        "no_trust": "Справедливо. Сначала почитай пару постов в канале — без регистрации, просто открой и оцени разбор сам.",
        "not_urgent": "Без спешки. Канал бесплатный, а ранние сигналы привязаны ко времени — это единственный нюанс.",
        "thinking": "Подумай спокойно. За какими лигами следишь больше всего? Подскажу, на какие разборы смотреть.",
    },
    "es": {
        "no_trust": "Válido. Leé algunos posts en el canal primero — sin registro, abrí y juzgá el análisis vos mismo.",
        "not_urgent": "Sin apuro. El canal es gratis y las señales tempranas dependen del tiempo — ese es el único detalle.",
        "thinking": "Tomate tu tiempo. ¿Qué ligas te gustan más? Te marco las lecturas correctas.",
    },
}

# ── Фоллбэки ──────────────────────────────────────────────────────────────────
GENERIC_FALLBACK = {
    "en": "📡 Pulling the latest — one sec.",
    "ru": "📡 Подтягиваю свежие данные — секунду.",
    "es": "📡 Buscando lo último — un segundo.",
}

FTD_CONFIRM_PROMPT = {
    "en": "Subscribed? Say yes and I'll point you to today's reads.",
    "ru": "Подписался? Скажи «да» — и подскажу, на какие разборы смотреть сегодня.",
    "es": "¿Te suscribiste? Decí sí y te marco las lecturas de hoy.",
}

MORNING_DIGEST_HEADER = {
    "en": "📅 *Good morning — today's fixtures*\n\n",
    "ru": "📅 *Доброе утро — матчи на сегодня*\n\n",
    "es": "📅 *Buen día — los partidos de hoy*\n\n",
}

MORNING_DIGEST_FOOTER = {
    "en": f"\n\n⚽ Full reads in the channel {CH}.",
    "ru": f"\n\n⚽ Полные разборы — в канале {CH}.",
    "es": f"\n\n⚽ Lecturas completas en el canal {CH}.",
}

# ── Нативное приглашение в канал + верификация ────────────────────────────────
JOIN_PROMPT = {
    "en": (
        "📣 *Subscribe to the channel*\n\nFull breakdowns, early signals and results — free. "
        "Tap subscribe, then come back and check access. 👇"
    ),
    "ru": (
        "📣 *Подписывайся на канал*\n\nПолные разборы, ранние сигналы и итоги — бесплатно. "
        "Нажми «Подписаться», затем вернись и проверь доступ. 👇"
    ),
    "es": (
        "📣 *Suscribite al canal*\n\nAnálisis completos, señales tempranas y resultados — gratis. "
        "Tocá suscribirte, después volvé y verificá el acceso. 👇"
    ),
}
JOIN_CHECK_BTN = {"en": "✅ I subscribed", "ru": "✅ Я подписался", "es": "✅ Ya me suscribí"}
JOIN_OK = {
    "en": "✅ Done — access unlocked. Full reads are waiting in the channel.",
    "ru": "✅ Готово — доступ открыт. Полные разборы ждут в канале.",
    "es": "✅ Listo — acceso desbloqueado. Las lecturas completas te esperan en el canal.",
}
JOIN_NOT_YET = {
    "en": "🔒 Don't see your subscription yet. Join the channel and tap “I subscribed” again.",
    "ru": "🔒 Пока не вижу подписки. Подпишись на канал и нажми «Я подписался» ещё раз.",
    "es": "🔒 Todavía no veo tu suscripción. Unite al canal y tocá «Ya me suscribí» de nuevo.",
}
