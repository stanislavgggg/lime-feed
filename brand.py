"""
brand.py — единый конфиг-слой бренда (backend)
================================================

Single source of truth для ВСЕГО, что отличается от бота к боту:
идентичность, персонаж/персона ИИ, вид спорта, оффер, ссылки, режим CTA
(вести в продукт ИЛИ в Telegram-канал), картинки воронки, язык/гео.

Архитектура «один движок — много брендов»:
    • Логика (bot.py, conversation.py, livescore.py, ai_agent.py …) НЕ меняется.
    • Меняется только активный объект BRAND.
    • Какой бренд активен — решает env-переменная BRAND_ID.
    • Секреты (токены, ключи API) сюда НЕ кладём — они остаются в окружении
      и читаются в config.py. brand.py хранит только НЕсекретную идентичность.

Поднять ещё одного бота = добавить запись в BRANDS + задеплоить инстанс
с BRAND_ID=<id> и своими BOT_TOKEN / ANTHROPIC_API_KEY / ключами API.

Совместимость: config.py превращён в тонкий шим, который реэкспортирует
поля BRAND под старыми именами (OFFER, COINPLAY_REG_URL, ESPORTS_GAMES …),
поэтому остальной код не требует правок.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from enum import Enum


# ──────────────────────────────────────────────────────────────────────────────
#  Перечисления
# ──────────────────────────────────────────────────────────────────────────────

def _handle_from_url(url: str) -> str:
    """t.me/<name> → '@<name>'. Приватные ссылки (t.me/+invite, /joinchat) → ''."""
    if not url:
        return ""
    tail = url.rstrip("/").split("/")[-1].strip()
    if not tail or tail.startswith("+") or tail.lower() == "joinchat":
        return ""
    return "@" + tail.lstrip("@")


class CTAMode(str, Enum):
    """Куда ведёт финальная кнопка воронки."""
    PRODUCT = "product"   # партнёрская ссылка (казино/букмекер) — как сейчас
    CHANNEL = "channel"   # подписка на Telegram-канал — новая воронка


class Vertical(str, Enum):
    """Основная спортивная вертикаль бренда (фильтрует данные и тексты)."""
    ESPORTS  = "esports"
    FOOTBALL = "football"
    BOTH     = "both"


# ──────────────────────────────────────────────────────────────────────────────
#  Вложенные конфиги
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Character:
    """Персонаж-аналитик, от лица которого говорит бот."""
    name: str                      # "Mateo"
    role: str                      # короткая роль для системного промпта
    persona: str                   # абзац характера (вставляется в system prompt)
    win_rate_display: float = 0.78  # отображаемая историческая точность (0..1)
    honest_stats: bool = False     # True → НЕ показывать дутый win_rate, только реальные
                                   # накопленные цифры (доверие = валюта конверсии в канал)


@dataclass(frozen=True)
class Offer:
    """Числа оффера. Используются и в текстах бота, и в строках оффера фронта."""
    bonus_pct: int = 100
    bonus_max: int = 5000
    free_spins: int = 80
    min_deposit: int = 20
    wagering: int = 40
    cashback_pct: int = 5
    currencies: int = 40
    currency: str = "USDT"

    def summary(self, lang: str = "en") -> str:
        """Однострочное резюме оффера для системного промпта ИИ."""
        return (
            f"{self.bonus_pct}% bonus up to {self.bonus_max} {self.currency} "
            f"+ {self.free_spins} free spins, min {self.min_deposit} {self.currency}, "
            f"{self.cashback_pct}% cashback, {self.currencies}+ cryptos"
        )


@dataclass(frozen=True)
class CTA:
    """
    Финальный призыв к действию.

    mode == PRODUCT → ведём в партнёрский продукт (registration_url / click_url).
    mode == CHANNEL → ведём в Telegram-канал (channel_url), оффер скрываем,
                      машина дожима FTD отключается (см. Funnel.repeat_enabled).
    """
    mode: CTAMode = CTAMode.PRODUCT

    # — режим PRODUCT —
    click_url: str = ""            # трекинговая ссылка (для дожимов/текста)
    registration_url: str = ""     # ссылка для кнопки «Зарегистрироваться»
    partner_name: str = ""         # "Coinplay"
    license_label: str = "Curacao licensed"
    license_url: str = ""
    since: str = "2022"

    # — режим CHANNEL —
    channel_url: str = ""          # "https://t.me/your_channel"
    channel_handle: str = ""       # "@your_channel" (для подписей)
    channel_id: str = ""           # для getChatMember: "@handle" или числовой "-100…".
                                   # Пусто → выводим из channel_handle / channel_url.
    gate: bool = False             # гейтить «полные разборы» / лучшие пики за подпиской.
                                   # Включает проверку членства в канале (см. membership.py)
                                   # и тизер-режим в /api/picks для неподписчиков.

    # — подписи кнопки по языкам —
    button_label: dict[str, str] = field(default_factory=lambda: {
        "en": "🎯 Register",
        "es": "🎯 Registrarme",
    })

    def primary_url(self) -> str:
        """Куда реально ведёт основная кнопка при текущем режиме."""
        return self.channel_url if self.mode is CTAMode.CHANNEL else self.registration_url

    def channel_chat_ref(self) -> str:
        """
        Идентификатор канала для Telegram getChatMember.
        Приоритет: явный channel_id → channel_handle → вывод @handle из channel_url.
        Возвращает '' если канал не настроен (тогда гейтинг просто отключается).
        """
        if self.channel_id:
            return self.channel_id
        if self.channel_handle:
            h = self.channel_handle.strip()
            return h if h.startswith("@") else "@" + h
        if self.channel_url:
            tail = self.channel_url.rstrip("/").split("/")[-1].strip()
            # пропускаем приглашения вида t.me/+abc — по ним getChatMember не работает
            if tail and not tail.startswith("+"):
                return "@" + tail.lstrip("@")
        return ""

    def label(self, lang: str) -> str:
        return self.button_label.get(lang, self.button_label.get("en", "Open"))


@dataclass(frozen=True)
class SportConfig:
    """Какие данные тянем у провайдера и как их показываем."""
    vertical: Vertical = Vertical.BOTH

    # Киберспорт: слаги PandaScore/ESportApi + человекочитаемые имена
    esports_games: tuple[str, ...] = ("cs2", "lol", "dota2", "valorant", "ow2", "r6")
    game_display: dict[str, str] = field(default_factory=lambda: {
        "cs2": "CS2", "csgo": "CS2", "lol": "League of Legends", "dota2": "Dota 2",
        "valorant": "Valorant", "ow2": "Overwatch 2", "r6siege": "Rainbow Six",
        "codmw": "Call of Duty", "rocketleague": "Rocket League",
    })

    # Футбол: лиги API-Football (название → league_id)
    football_leagues: dict[str, int] = field(default_factory=lambda: {
        "Champions League": 2, "Premier League": 39, "La Liga": 140,
        "Copa Libertadores": 13, "Liga 1 Peru": 268, "Liga BetPlay CO": 239,
        "Primera Division AR": 130, "V.League VN": 340, "ISL India": 323,
    })

    def wants_esports(self) -> bool:
        return self.vertical in (Vertical.ESPORTS, Vertical.BOTH)

    def wants_football(self) -> bool:
        return self.vertical in (Vertical.FOOTBALL, Vertical.BOTH)


@dataclass(frozen=True)
class Funnel:
    """Механика воронки (тюнингуется под бренд)."""
    max_daily_picks: int = 3
    onboarding_turns: int = 2
    repeat_enabled: bool = True        # машина повторных дожимов после FTD
    repeat_schedule: tuple[int, ...] = (3_600, 21_600, 86_400, 259_200, 604_800)


@dataclass(frozen=True)
class I18n:
    """Языки и сопоставление гео/языков Telegram. English = приоритетный дефолт."""
    supported: tuple[str, ...] = ("en", "ru", "es")
    default: str = "en"   # приоритет: неизвестный язык профиля → английский
    geo_lang: dict[str, str] = field(default_factory=lambda: {
        "VN": "en", "IN": "en", "PE": "es", "CO": "es", "AR": "es",
        "RU": "ru", "BY": "ru", "KZ": "ru", "UA": "ru",
    })
    tg_lang_map: dict[str, str] = field(default_factory=lambda: {
        # язык профиля Telegram → язык контента (всё прочее → default=en)
        "en": "en", "vi": "en", "hi": "en",
        "es": "es",
        "ru": "ru", "uk": "ru", "be": "ru", "kk": "ru",
    })


@dataclass(frozen=True)
class Brand:
    """
    Корневой объект бренда. Всё, что различается между ботами, живёт тут.
    Поля имён зеркалят brand.config.ts на фронте — это один конфиг на двух языках.
    """
    id: str
    display_name: str                   # "MetaPlay"
    bot_username: str                    # "MetaPlayBot"
    tagline: dict[str, str]             # подзаголовок/слоган по языкам
    character: Character
    sport: SportConfig
    offer: Offer
    cta: CTA
    funnel: Funnel = field(default_factory=Funnel)
    i18n: I18n = field(default_factory=I18n)
    privacy_url: str = ""

    # Картинки воронки: момент → файл в pics/ (переопределяет media.MOMENT_PICS)
    images: dict[str, str] = field(default_factory=lambda: {
        "start": "19.png", "onboarding1": "110.png", "onboarding2": "111.png",
        "bridge": "113.png", "cta": "114.png", "ftd": "112.png",
        "morning": "115.png", "picks": "114.png",
        "repeat_hot": "116.png", "repeat_win": "117.png",
    })

    # Имя модуля с пакетом текстов (см. «Пакеты копирайта» ниже).
    copy_pack: str = "messages"

    def with_env_overrides(self) -> "Brand":
        """
        Позволяет переопределить ссылки/режим из окружения на конкретном деплое
        без правки кода (удобно для A/B и быстрых смен оффера):
            CTA_MODE=channel CHANNEL_URL=https://t.me/foo
            CHANNEL_ID=@foo  CTA_GATE=true  HONEST_STATS=true
            COINPLAY_URL=... COINPLAY_REG_URL=...
        """
        cta = self.cta
        env_mode = os.environ.get("CTA_MODE")
        if env_mode in (CTAMode.PRODUCT.value, CTAMode.CHANNEL.value):
            cta = replace(cta, mode=CTAMode(env_mode))

        def _envbool(name: str, default: bool) -> bool:
            raw = os.environ.get(name)
            if raw is None:
                return default
            return raw.strip().lower() in ("1", "true", "yes", "on")

        # ── Резолв канала ────────────────────────────────────────────────────
        # Задать канал можно ОДНОЙ переменной CHANNEL_URL (публичный t.me/<name>):
        # из неё выводится @handle для отображения и проверки подписки.
        # Для приватного канала (t.me/+invite) задай ещё CHANNEL_ID=-100… .
        env_url    = os.environ.get("CHANNEL_URL")
        env_handle = os.environ.get("CHANNEL_HANDLE")
        env_id     = os.environ.get("CHANNEL_ID")

        new_url = env_url if env_url is not None else cta.channel_url
        if env_handle:
            h = env_handle.strip()
            new_handle = h if h.startswith("@") else "@" + h
        elif env_url:
            # handle явно не задан → выводим из заданного URL (если он публичный)
            new_handle = _handle_from_url(env_url) or cta.channel_handle
        else:
            new_handle = cta.channel_handle

        cta = replace(
            cta,
            click_url=os.environ.get("COINPLAY_URL", cta.click_url),
            registration_url=os.environ.get("COINPLAY_REG_URL", cta.registration_url),
            channel_url=new_url,
            channel_handle=new_handle,
            channel_id=env_id if env_id is not None else cta.channel_id,
            gate=_envbool("CTA_GATE", cta.gate),
        )
        character = replace(
            self.character,
            honest_stats=_envbool("HONEST_STATS", self.character.honest_stats),
        )
        return replace(
            self,
            cta=cta,
            character=character,
            bot_username=os.environ.get("BOT_USERNAME", self.bot_username),
            privacy_url=os.environ.get("PRIVACY_URL", self.privacy_url),
        )


# ──────────────────────────────────────────────────────────────────────────────
#  Реестр брендов
# ──────────────────────────────────────────────────────────────────────────────

_COINPLAY_LINK = "https://promotioncoinplay.com/L?tag=d_5617175m_59419c_&site=5617175&ad=59419"

#: Бренд №1 — АКТИВНЫЙ: киберспорт + футбол, цель = ПОДПИСКА НА КАНАЛ.
METAPLAY = Brand(
    id="metaplay",
    display_name="MetaPlay",
    bot_username="MetaPlayBot",
    tagline={
        "en": "Read the game before it starts.",
        "es": "Leé el partido antes de que empiece.",
    },
    character=Character(
        name="Mateo",
        role="esports and football analyst",
        persona=(
            "You are {name} — {role} for the {brand} Telegram channel. "
            "Tone: insider, sharp, genuine — an analyst who shares his reads, not a promoter. "
            "You do NOT advertise casinos or bookmakers and never tell people to bet or deposit. "
            "Your goal is to get people to subscribe to the {brand} channel, "
            "where full breakdowns, early signals and results are posted."
        ),
        honest_stats=True,   # канал: только реальные накопленные цифры, без дутых процентов
    ),
    sport=SportConfig(vertical=Vertical.BOTH),
    offer=Offer(),  # в channel-режиме оффер не показывается
    cta=CTA(
        mode=CTAMode.CHANNEL,
        # ┌──────────────────────────────────────────────────────────────────────┐
        # │  ⚠️  ЕДИНСТВЕННОЕ МЕСТО, ГДЕ ЗАДАЁТСЯ РЕАЛЬНЫЙ КАНАЛ (backend).         │
        # │  Замени @your_channel на свой. Или задай env CHANNEL_URL / CHANNEL_ID. │
        # │  Бот ДОЛЖЕН быть админом этого канала — иначе проверка подписки не    │
        # │  работает (getChatMember).                                            │
        # └──────────────────────────────────────────────────────────────────────┘
        channel_url="https://t.me/your_channel",
        channel_handle="@your_channel",
        gate=True,   # полные разборы / лучшие пики открываются только подписчикам
        button_label={
            "en": "📣 Join the channel",
            "ru": "📣 Подписаться на канал",
            "es": "📣 Unirme al canal",
        },
    ),
    funnel=Funnel(repeat_enabled=False),   # канал не дожимаем на депозит
    privacy_url="https://arenafronend.s26636274.workers.dev/privacy",
    copy_pack="copy_metaplay_channel",
)

#: Бренд №2 — пример ремикса: только футбол, финал ведёт в Telegram-КАНАЛ.
#  Демонстрирует ровно твою задачу: другой вид спорта, другой персонаж,
#  последняя страница = подписка на канал (продукт скрыт, дожимы FTD выключены).
GOALCAST = Brand(
    id="goalcast",
    display_name="GoalCast",
    bot_username="GoalCastBot",
    tagline={
        "en": "Football reads, every matchday.",
        "es": "Lecturas de fútbol, cada jornada.",
    },
    character=Character(
        name="Diego",
        role="football analyst",
        persona=(
            "You are {name} — {role} running the {brand} Telegram channel. "
            "Tone: passionate, data-driven, no hype. You break down matches "
            "and invite people to follow the channel for the full reads."
        ),
        win_rate_display=0.74,
        honest_stats=True,   # канал: показываем только реальные накопленные цифры
    ),
    sport=SportConfig(vertical=Vertical.FOOTBALL),
    offer=Offer(),  # в channel-режиме оффер не показывается, но поле остаётся валидным
    cta=CTA(
        mode=CTAMode.CHANNEL,
        channel_url="https://t.me/goalcast_channel",
        channel_handle="@goalcast_channel",
        gate=True,   # лучшие пики/полные разборы открываются только подписчикам
        button_label={"en": "📣 Join the channel", "es": "📣 Unite al canal"},
    ),
    funnel=Funnel(repeat_enabled=False),   # канал не дожимаем на депозит
    privacy_url="https://goalcast.example.workers.dev/privacy",
    copy_pack="copy_goalcast",
)

#: Бренд №3 — KINETIC FEED: новостной + live-score продукт.
#  Персона — не типстер, а нейтральный новостной/score-ведущий «Kit». Цель воронки —
#  ПОДПИСКА на канал. Никаких ставок/депозитов. Это активный бренд по умолчанию.
KINETIC = Brand(
    id="kinetic",
    display_name="Kinetic Feed",
    bot_username="KineticFeedBot",
    tagline={
        "en": "News & live scores, the moment they break.",
        "es": "Noticias y resultados en vivo, al instante.",
    },
    character=Character(
        name="Kit",
        role="news & live-score anchor",
        persona=(
            "You are {name} — {role} for the {brand} Telegram channel. "
            "Tone: fast, clear, neutral newsroom energy — you report, you don't hype. "
            "You cover crypto, the casino/iGaming industry, esports and football: "
            "headlines, live scores and results. "
            "You do NOT give betting tips or financial advice and never tell anyone to "
            "bet, deposit or buy anything. "
            "Your goal is to get people to subscribe to the {brand} channel, where the "
            "full feed, instant breaking alerts and live-score pushes are posted."
        ),
        honest_stats=True,
    ),
    sport=SportConfig(vertical=Vertical.BOTH),
    offer=Offer(),  # в channel-режиме оффер не показывается
    cta=CTA(
        mode=CTAMode.CHANNEL,
        # ┌──────────────────────────────────────────────────────────────────────┐
        # │  ⚠️  ЕДИНСТВЕННОЕ МЕСТО, ГДЕ ЗАДАЁТСЯ РЕАЛЬНЫЙ КАНАЛ (backend).         │
        # │  Замени @your_channel на свой ИЛИ задай env CHANNEL_URL / CHANNEL_ID.  │
        # │  Бот ДОЛЖЕН быть админом канала — иначе getChatMember не работает.     │
        # └──────────────────────────────────────────────────────────────────────┘
        channel_url="https://t.me/your_channel",
        channel_handle="@your_channel",
        gate=True,   # часть ленты/полный фид открывается только подписчикам
        button_label={
            "en": "📣 Join the channel",
            "ru": "📣 Подписаться на канал",
            "es": "📣 Unirme al canal",
        },
    ),
    funnel=Funnel(repeat_enabled=False),   # канал не дожимаем
    privacy_url="https://arenafronend.s26636274.workers.dev/privacy",
    copy_pack="copy_kinetic",
)

#: Бренд №4 — GREEN LIME FEED: фокус на деньгах/маркетах (зелёный = деньги).
#  Персона — зелёный лайм-маскот «Limo», помешанный на том, «куда движутся деньги».
#  ВАЖНО (Telegram Ads compliance): только НОВОСТИ и ЦИФРЫ. Никаких фин/беттинг-советов,
#  призывов покупать/продавать/ставить и обещаний прибыли/доходности. Цель — ПОДПИСКА на канал.
GREENLIME = Brand(
    id="greenlime",
    display_name="Green Lime Feed",
    bot_username="GreenLimeFeedBot",
    tagline={
        "en": "Follow the money — markets, deals & live scores.",
        "es": "Seguí el dinero — mercados, acuerdos y resultados en vivo.",
    },
    character=Character(
        name="Limo",
        role="money-news & live-score anchor",
        persona=(
            "You are {name} — {role} for the {brand} Telegram channel. "
            "{name} is a cheeky green lime mascot obsessed with where the money moves. "
            "Tone: punchy, energetic, money-savvy newsroom — you report the numbers and "
            "the deals, you don't hype. You cover the MONEY side of crypto, the "
            "casino/iGaming industry, esports and football: market moves, big deals, "
            "prize pools, sponsorships, transfers, who's up and who's down. "
            "STRICT COMPLIANCE: you do NOT give financial or betting advice, never tell "
            "anyone to buy, sell, bet or deposit, and NEVER promise profit, returns or "
            "winnings. Everything is informational news only. "
            "Your goal is to get people to subscribe to the {brand} channel, where the "
            "full money feed, instant market alerts and live-score pushes are posted."
        ),
        honest_stats=True,
    ),
    sport=SportConfig(vertical=Vertical.BOTH),
    offer=Offer(),  # в channel-режиме оффер не показывается
    cta=CTA(
        mode=CTAMode.CHANNEL,
        # ┌──────────────────────────────────────────────────────────────────────┐
        # │  ⚠️  ЕДИНСТВЕННОЕ МЕСТО, ГДЕ ЗАДАЁТСЯ РЕАЛЬНЫЙ КАНАЛ (backend).         │
        # │  Замени @your_channel на свой ИЛИ задай env CHANNEL_URL / CHANNEL_ID.  │
        # │  Бот ДОЛЖЕН быть админом канала — иначе getChatMember не работает.     │
        # └──────────────────────────────────────────────────────────────────────┘
        channel_url="https://t.me/your_channel",
        channel_handle="@your_channel",
        gate=True,
        button_label={
            "en": "💚 Join the channel",
            "ru": "💚 Подписаться на канал",
            "es": "💚 Unirme al canal",
        },
    ),
    funnel=Funnel(repeat_enabled=False),
    privacy_url="https://arenafronend.s26636274.workers.dev/privacy",
    copy_pack="copy_greenlime",
)

#: Все доступные бренды.
BRANDS: dict[str, Brand] = {
    GREENLIME.id: GREENLIME,
    KINETIC.id: KINETIC,
    METAPLAY.id: METAPLAY,
    GOALCAST.id: GOALCAST,
}


# ──────────────────────────────────────────────────────────────────────────────
#  Выбор активного бренда
# ──────────────────────────────────────────────────────────────────────────────

_active_id = os.environ.get("BRAND_ID", GREENLIME.id).strip().lower()
if _active_id not in BRANDS:
    raise RuntimeError(
        f"Unknown BRAND_ID={_active_id!r}. Available: {', '.join(BRANDS)}"
    )

#: Активный бренд этого инстанса (с применёнными env-оверрайдами).
BRAND: Brand = BRANDS[_active_id].with_env_overrides()
