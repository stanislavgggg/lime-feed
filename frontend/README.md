# Frontend integration — channel funnel

Drop-in client for the backend funnel endpoints. Two files:

- `funnel-client.ts` — framework-agnostic typed client (membership, events, gated picks, bot-routed join).
- `useFunnel.ts` — React hook that wires it into a component, including **instant unlock on return** from the channel.

## API contract (served by `api.py`)

| Endpoint | Purpose | Lever |
|---|---|---|
| `GET /api/picks?lang=en&uid=<id>` | picks; non-subscribers get pick #1 free + teasers, rest `locked:true` | #3 |
| `GET /api/membership?uid=<id>` | `getChatMember` check → `{member}` | #1 |
| `POST /api/event {event,uid,meta}` | funnel events (`cta_view`/`cta_tap`/`channel_open`/…) | #5 |
| `GET /api/funnel` | counters + conversion rates (admin/CRO) | #5 |
| `GET /api/stats` | honest track record (`rate:null` while accumulating) | #6 |

## The flow that converts (levers 1–3 together)

1. Show picks. Pick #1 is free (reciprocity — value first). The rest render as a **blur-lock** using `pick.locked` + the teaser in `pick.reasoning`.
2. On the wall / lock, call `startJoin()` → opens `t.me/<bot>?start=join`. The **bot** sends a native message with the Join button + "✅ I subscribed" (lever #2 — conversion stays inside Telegram, no webview context-switch).
3. When the user comes back to the mini-app, the hook re-checks membership on `focus`/`visibilitychange` and **unlocks instantly** (lever #1).

## Wiring

```ts
const f = useFunnel({ baseUrl: import.meta.env.VITE_API_BASE, botUsername: "GoalCastBot", lang: "en" });

useEffect(() => { f.event("cta_view"); }, []);     // fire when the CTA becomes visible
// f.picks / f.gate.locked / f.startJoin() / f.member
```

Fire `f.event("channel_open")` right before `startJoin()` if you want to separate "tapped CTA" from "left for the channel" in the funnel.

## Required env on the backend

```
CTA_MODE=channel
CHANNEL_URL=https://t.me/your_channel
CHANNEL_ID=@your_channel     # bot MUST be admin of this channel
CTA_GATE=true
HONEST_STATS=true
MINI_APP_ORIGIN=https://your-miniapp.example   # CORS
```

> ⚠️ `getChatMember` only works if the bot is an **administrator** of the channel and the user has started the bot at least once (which they have, since they arrived from it).
