# Arena Bot Engine — мультибрендовый движок Telegram-ботов

Один технический бэкенд → много ботов (разные виды спорта, персонажи, воронки)
без форка логики. Всё, что отличается между ботами, лежит в **`brand.py`**.

## Что внутри

- **Telegram-бот** (`bot.py`, `conversation.py`, `ai_agent.py`, `onboarding.py`,
  `ftd_onboarding.py`, `signals.py`) — воронка + ИИ-персонаж-аналитик.
- **HTTP API** (`api.py`) — отдаёт мини-аппке данные:
  `/api/health`, `/api/live`, `/api/upcoming`, `/api/picks?lang=en[&uid=]`, `/api/stats`,
  `/api/membership?uid=` (проверка подписки), `POST /api/event` (аналитика),
  `/api/funnel` (счётчики воронки).
- **Подписка на канал** (`membership.py`, `analytics.py`) — гейтинг контента за
  подпиской (getChatMember), нативная верификация в боте, событийная аналитика для CRO.
- **Данные** (`livescore.py`) — киберспорт (PandaScore/ESportApi) + футбол (API-Football).

## Конфиг-слой (single source of truth)

| Файл | Что задаёт |
|------|------------|
| `brand.py` | реестр брендов: идентичность, персонаж, оффер, вид спорта, **режим CTA (product / channel)**, ссылки, картинки, язык |
| `config.py` | тонкий шим: секреты из env + значения из активного `BRAND` под старыми именами |
| `copy_<brand>.py` | пакет текстов (голос персонажа) на бренд |
| `messages.py` | загрузчик: подхватывает `copy_<brand>.py` по `BRAND.copy_pack` |

Активный бренд выбирается переменной `BRAND_ID` (см. `.env.example`).

## Запуск локально

```bash
pip install -r requirements.txt
cp .env.example .env            # заполнить токены/ключи
python bot.py                   # бот
python api.py                   # API (в отдельном процессе)
```

## Деплой (Render)

`render.yaml` поднимает два сервиса: `arena-bot` (worker) и `arena-api` (web).
Для каждого нового бота — отдельный инстанс с своим `BRAND_ID` + секретами.

## Добавить нового бота «на потоке»

1. **`brand.py`** → добавить запись в `BRANDS` (скопировать `METAPLAY` или `GOALCAST`,
   поменять id, имя, персонажа, вид спорта, `cta.mode`, ссылки).
2. **`copy_<id>.py`** → создать пакет текстов (образец: `copy_metaplay.py`,
   для канала — `copy_goalcast.py`). Указать `copy_pack="copy_<id>"`.
3. **`pics/`** → положить картинки персонажа, прописать в `BRAND.images`.
4. Задеплоить инстанс с `BRAND_ID=<id>`, своим `BOT_TOKEN`, `ANTHROPIC_API_KEY`,
   ключами API. Логику не трогаем.

`cta.mode="channel"` автоматически: ведёт финальную кнопку в Telegram-канал,
скрывает оффер и **отключает дожимы FTD** (`funnel.repeat_enabled=False`).

## Встроенные бренды (примеры)

- **`metaplay`** — киберспорт + футбол, ведём в продукт (Coinplay). Персонаж Mateo.
- **`goalcast`** — только футбол, ведём в Telegram-канал. Персонаж Diego.
