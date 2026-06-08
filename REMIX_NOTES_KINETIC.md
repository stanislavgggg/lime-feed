# Kinetic Feed remix — what changed (bot)

This backend was remixed from the "MetaPlay / Mateo" betting-tips bot into **Kinetic Feed**, a
news + live-score Telegram product whose only conversion goal is **channel subscription**.
The shared HTTP API (`api.py`) and its data modules are unchanged — the Mini App keeps working.

## Active brand
`brand.py` now defaults to the new **`kinetic`** brand (`BRAND_ID=kinetic`):
- Persona **Kit** — a neutral news/live-score anchor (no betting/financial advice).
- Copy pack **`copy_kinetic.py`** (en/ru/es), all CTAs drive to the channel.
- The old `metaplay` and `goalcast` brands are still in the registry for reference.

## Bot product changes
- **Menu** → 🔴 Live Scores · 📰 News · 📅 Upcoming · 📣 Channel (en/ru/es; RU menu added).
- **News is wired into the bot** (was API-only): `/news` command + 📰 News button, an inline
  category switch (All / Crypto / Casino / Esports), a market header (Fear & Greed + BTC/ETH/SOL)
  and ~6 linked headlines. Built by `news.format_news_message(...)`, fail-soft.
- **Locked preview** → non-subscribers see the digest preview + a "full feed in the channel"
  footer and a Join button; the live-scores screen carries a channel nudge too.
- **Onboarding** reframed to news interests (topics + teams/leagues/coins to highlight).
- **Removed** the betting identity from the bot: Picks and Track Record buttons/commands gone,
  and the casino-deposit machinery (FTD detection, deposit celebration, repeat-push, daily
  picks broadcast) no longer runs. `predictions.py` stays only because `/api/picks` uses it.
- Subscription verification (`✅ I subscribed` → `getChatMember`) is the conversion event; kept.

## Configure before deploy
Set the channel in **one** place — either edit `PULSE.cta.channel_url` in `brand.py`, or via env:
```
BRAND_ID=kinetic
CHANNEL_URL=https://t.me/your_channel      # public channel
# CHANNEL_ID=-100123...                    # only for private channels
CTA_GATE=true
BOT_TOKEN=...        ANTHROPIC_API_KEY=...
RAPIDAPI_KEY=...                            # live football + esports scores
```
The bot must be an **admin** of the channel for subscription checks to work.

Run: `python bot.py` (Telegram bot) and `python api.py` (Mini App HTTP API) as before.
