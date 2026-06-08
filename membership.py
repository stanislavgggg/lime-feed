"""
membership.py — проверка подписки на канал (рычаг №1 воронки)
==============================================================

Самый сильный механик роста: подписка перестаёт быть «просьбой» и становится
«ключом». Бот (который уже является админом канала) спрашивает у Telegram, состоит
ли пользователь в канале — getChatMember — и на этом строится гейтинг:
лучшие пики / полные разборы открываются только подписчикам.

Один общий модуль для двух процессов:
    • api.py   → эндпоинт GET /api/membership?uid= (мини-апп разблокирует контент);
    • bot.py   → колбэк «✅ Я подписался» проверяет членство и подтверждает доступ.

Требования к окружению:
    • BOT_TOKEN — бот должен быть АДМИНОМ канала, иначе getChatMember вернёт ошибку.
    • CHANNEL_CHAT_REF — '@handle' или числовой '-100…' (выводится в brand.py из cta).

Кэш: положительный результат держим 10 минут (членство меняется редко),
отрицательный НЕ кэшируем — чтобы «подписался → разблокировалось» срабатывало мгновенно.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from config import BOT_TOKEN, CHANNEL_CHAT_REF

logger = logging.getLogger(__name__)

_API = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"

# Статусы, которые считаем «подписан».
_MEMBER_STATUSES = {"creator", "administrator", "member"}

# uid -> (is_member, expires_at). Только положительные результаты.
_cache: dict[int, tuple[bool, float]] = {}
_POSITIVE_TTL = 600.0  # сек


def channel_configured() -> bool:
    """Гейтинг возможен только если канал настроен (есть реальный @handle / id).
    Плейсхолдер 'your_channel' настоящим каналом не считаем — иначе гейт запер бы
    контент против несуществующего канала ещё до настройки."""
    ref = (CHANNEL_CHAT_REF or "").strip()
    if not ref or "your_channel" in ref.lower():
        return False
    return True


async def is_member(uid: int, *, use_cache: bool = True) -> bool:
    """
    True, если пользователь uid состоит в канале бренда.

    Безопасно к сбоям: при любой ошибке сети/прав возвращает False
    (контент остаётся «заблокированным» — это не ломает воронку, лишь не разблокирует).
    Если канал не настроен — возвращает True (гейтинг фактически выключен,
    чтобы не запирать контент вообще без причины).
    """
    if not channel_configured():
        return True

    now = time.time()
    if use_cache:
        cached = _cache.get(uid)
        if cached and cached[1] > now:
            return cached[0]

    params = {"chat_id": CHANNEL_CHAT_REF, "user_id": uid}
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(_API, params=params)
        data = resp.json()
    except Exception as e:
        logger.warning(f"getChatMember network error uid={uid}: {e}")
        return False

    if not data.get("ok"):
        # Частые причины: бот не админ канала, неверный chat_id, юзер не стартовал бота.
        logger.warning(f"getChatMember not ok uid={uid}: {data.get('description')}")
        return False

    result = data.get("result", {})
    status = result.get("status", "")
    member = status in _MEMBER_STATUSES
    # 'restricted' считается подписанным только если is_member=True
    if status == "restricted":
        member = bool(result.get("is_member", False))

    if member:
        _cache[uid] = (True, now + _POSITIVE_TTL)

    return member


def invalidate(uid: int) -> None:
    """Сбросить кэш для пользователя (например, после явной проверки в боте)."""
    _cache.pop(uid, None)
