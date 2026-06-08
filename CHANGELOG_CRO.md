# CRO changelog — channel subscription funnel

Implements the six conversion levers from the funnel analysis on the backend
(bot + mini-app API), plus a drop-in frontend client. Single-source-of-truth
philosophy preserved: everything brand-specific stays in `brand.py`.

## What changed

### New modules
- **`membership.py`** — `getChatMember` check with a short-lived positive cache
  (negatives never cached → instant unlock). Fails safe (blocked = not unlocked).
- **`analytics.py`** — JSON funnel counters shared by the bot and API processes;
  unique-join dedup; `snapshot()` with tap/view, join/tap, join/view rates.
- **`frontend/`** — `funnel-client.ts`, `useFunnel.ts`, `README.md` (the mini-app
  half of the contract; this repo is the backend).

### Lever 1 — gating via getChatMember
- `CTA.channel_id` + `CTA.channel_chat_ref()` in `brand.py`; `CTA.gate` flag.
- `GET /api/membership?uid=` endpoint.
- Bot "✅ I subscribed" callback verifies and unlocks in place.

### Lever 2 — convert through the bot, not the webview
- `/start join` deep link + `/join` command → native message with Join + verify buttons.
- Unified `_cta_keyboard()` adds the verify button in channel mode everywhere a CTA shows.
- Frontend `startJoin()` opens `t.me/<bot>?start=join`.

### Lever 3 — teaser / blur-lock on reasoning
- `apply_gate()` in `predictions.py`: first pick free, rest become teasers + `locked:true`.
- `/api/picks?uid=` returns a `gate` object for the frontend wall.

### Lever 5 — analytics (measure before tuning)
- `POST /api/event`, `GET /api/funnel`, admin `/funnel` command.
- Events: `cta_view`, `cta_tap`, `channel_open`, `membership_check`, `join_confirmed`.

### Lever 6 — trust / honest stats
- `Character.honest_stats` (default on for the channel brand): no dressed-up win rate;
  `/api/stats` returns `rate:null` + `note:"accumulating"` until ≥5 real picks.
- Picks header/footer are mode-aware (no affiliate link leaks into channel mode).

### Bug fix (was blocking the funnel)
- Restored `_safe_md()` in `predictions.py` — it was called but undefined (its body had
  been merged into `_md_url`'s dead code), so any non-empty picks raised `NameError`.
- `get_stats_display()` now uses the brand's character name instead of hardcoded "Mateo".

## New env vars
`CHANNEL_ID`, `CTA_GATE`, `HONEST_STATS`, `ANALYTICS_FILE` — see `.env.example`.

## Validation run
- All modules import in both brands (metaplay/product, goalcast/channel).
- Logic tested: `apply_gate` (teaser + no source mutation), `analytics` counters/rates,
  honest `_stats_payload`, `format_predictions_message` (no affiliate leak in channel mode).
- HTTP handler tested with fake streams: POST body parsing, routing, 400s, OPTIONS preflight.

## Not in this repo
The mini-app frontend (`brand.config.ts`, `PicksTab`, `metaplay.ts`) is a separate
project. The `frontend/` folder here is the client + contract to wire it in.
