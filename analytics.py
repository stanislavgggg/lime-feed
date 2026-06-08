"""
analytics.py — событийная аналитика воронки (рычаг №5)
=======================================================

«Без замеров CRO — это гадание.» Этот модуль даёт минимальный, но достаточный
слой событий, чтобы мерить и A/B-тестировать формулировки/места триггеров,
а не крутить их «по ощущениям».

Хранилище — простой JSON-счётчик (тот же паттерн, что и storage.py), общий для
процессов api.py и bot.py (один контейнер → одна файловая система).

Воронка подписки на канал:
    cta_view        — показали CTA «подписаться»
    cta_tap         — тапнули CTA
    channel_open    — открыли канал (из мини-аппа/сообщения бота)
    membership_check— была проверка членства (getChatMember)
    join_confirmed  — фактически подтверждённая подписка (UNIQUE по uid)

join_confirmed считается по уникальным пользователям — это и есть «настоящая»
конверсия, в отличие от тапов по кнопке.
"""
from __future__ import annotations

import json
import logging
import os
import time

logger = logging.getLogger(__name__)

ANALYTICS_FILE = os.environ.get("ANALYTICS_FILE", "analytics.json")

# Канонический порядок событий воронки (для красивого снапшота).
FUNNEL_EVENTS = ("cta_view", "cta_tap", "channel_open", "membership_check", "join_confirmed")

_data: dict = {"events": {}, "joined_uids": []}
_last_save = 0.0
_SAVE_INTERVAL = 2.0


def _load() -> None:
    global _data
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE) as f:
                loaded = json.load(f)
            _data = {
                "events": dict(loaded.get("events", {})),
                "joined_uids": list(loaded.get("joined_uids", [])),
            }
        except Exception as e:
            logger.error(f"Analytics load error: {e}")


def _save(force: bool = False) -> None:
    global _last_save
    now = time.time()
    if not force and now - _last_save < _SAVE_INTERVAL:
        return
    _last_save = now
    try:
        tmp = ANALYTICS_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(_data, f, indent=2)
        os.replace(tmp, ANALYTICS_FILE)
    except Exception as e:
        logger.error(f"Analytics save error: {e}")


_load()


def track(event: str, uid: int | None = None, meta: dict | None = None) -> None:
    """Инкремент счётчика события. uid/meta — необязательны (для будущей детализации)."""
    if not event or not isinstance(event, str) or len(event) > 64:
        return
    events = _data.setdefault("events", {})
    events[event] = events.get(event, 0) + 1
    _save()


def mark_join(uid: int) -> bool:
    """
    Отметить подтверждённую подписку. Возвращает True, если это НОВЫЙ пользователь
    (тогда инкрементим уникальный join_confirmed). Идемпотентно по uid.
    """
    uids = _data.setdefault("joined_uids", [])
    if uid in uids:
        return False
    uids.append(uid)
    events = _data.setdefault("events", {})
    events["join_confirmed"] = events.get("join_confirmed", 0) + 1
    _save(force=True)
    return True


def snapshot() -> dict:
    """Счётчики воронки + производные конверсии — для /api/funnel и /funnel в боте."""
    events = _data.get("events", {})
    counts = {e: int(events.get(e, 0)) for e in FUNNEL_EVENTS}
    # плюс любые кастомные события вне канонического списка
    extra = {k: int(v) for k, v in events.items() if k not in FUNNEL_EVENTS}

    def _rate(num: str, den: str) -> float | None:
        d = counts.get(den, 0)
        return round(counts.get(num, 0) / d * 100, 1) if d else None

    return {
        "funnel": counts,
        "extra": extra,
        "unique_joins": len(_data.get("joined_uids", [])),
        "rates": {
            "tap_per_view":  _rate("cta_tap", "cta_view"),
            "join_per_tap":  _rate("join_confirmed", "cta_tap"),
            "join_per_view": _rate("join_confirmed", "cta_view"),
        },
    }
