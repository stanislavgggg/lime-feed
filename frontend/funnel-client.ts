/**
 * funnel-client.ts — drop-in client for the arena-bot-engine funnel API
 * =====================================================================
 *
 * Mirrors the backend contract (api.py) for the three CRO levers that live in
 * the mini-app: membership gating (#1), bot-routed conversion (#2), and
 * event analytics (#5). Framework-agnostic; a thin React hook is at the bottom.
 *
 * The Telegram user id comes from the Mini App SDK:
 *   window.Telegram.WebApp.initDataUnsafe.user.id
 *
 * Usage:
 *   const api = createFunnelClient({ baseUrl: import.meta.env.VITE_API_BASE, uid });
 *   await api.event("cta_view");
 *   const { picks, gate } = await api.picks("en");
 *   if (gate.locked) showSubscribeWall();
 *   const { member } = await api.membership();   // poll after the user returns from the channel
 */

export type Lang = "en" | "es";

export interface Pick {
  match: string;
  game: string;
  pick: string;
  reasoning: string;       // teaser (truncated) when locked === true
  confidence: "High" | "Medium" | "Low";
  locked: boolean;         // true → full read is behind the subscription wall
}

export interface Stats {
  correct: number;
  total: number;
  rate: number | null;     // null while accumulating (honest-stats mode)
  note: "accumulating" | "real";
}

export interface GateInfo {
  enabled: boolean;
  locked: boolean;         // true → at least one pick is gated for this user
  is_member: boolean;
  channel: string;         // "@handle" or t.me URL
}

export interface PicksResponse {
  picks: Pick[];
  stats: Stats;
  source: "real" | "no_matches";
  gate: GateInfo;
}

export interface MembershipResponse {
  uid: number;
  member: boolean;
  gate: boolean;
  channel: string;
  configured: boolean;
}

/** Canonical funnel events the backend understands. Use these — they map to /api/funnel. */
export type FunnelEvent =
  | "cta_view"
  | "cta_tap"
  | "channel_open"
  | "membership_check"
  | "join_confirmed"
  | (string & {}); // allow custom events; they land in snapshot.extra

export interface FunnelClientOptions {
  baseUrl: string;
  uid?: number;
}

export function createFunnelClient(opts: FunnelClientOptions) {
  const base = opts.baseUrl.replace(/\/$/, "");
  const uid = opts.uid;

  async function getJSON<T>(path: string): Promise<T> {
    const res = await fetch(`${base}${path}`);
    if (!res.ok) throw new Error(`${path} → ${res.status}`);
    return res.json() as Promise<T>;
  }

  return {
    uid,

    /** Fire a funnel event (lever #5). Non-blocking, never throws — analytics must not break UX. */
    event(event: FunnelEvent, meta?: Record<string, unknown>): void {
      try {
        const body = JSON.stringify({ event, uid, meta });
        // keepalive lets the beacon survive a tab/route change (e.g. opening the channel)
        fetch(`${base}/api/event`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body,
          keepalive: true,
        }).catch(() => {});
      } catch {
        /* swallow — analytics is best-effort */
      }
    },

    /** Picks, gated for non-subscribers (lever #3). Pass uid to unlock for members. */
    picks(lang: Lang = "en"): Promise<PicksResponse> {
      const q = uid ? `&uid=${uid}` : "";
      return getJSON<PicksResponse>(`/api/picks?lang=${lang}${q}`);
    },

    /** Live subscription check via getChatMember (lever #1). Poll after the user returns from the channel. */
    membership(): Promise<MembershipResponse> {
      if (!uid) return Promise.reject(new Error("uid required for membership check"));
      return getJSON<MembershipResponse>(`/api/membership?uid=${uid}`);
    },

    stats(): Promise<Stats> {
      return getJSON<Stats>(`/api/stats`);
    },

    /**
     * Route conversion through the bot (lever #2): opens t.me/<bot>?start=join so the bot
     * sends a native message with the Join button + "✅ I subscribed" verifier — one flow,
     * no context-switch out of Telegram. Falls back to opening the channel link directly.
     */
    openJoinViaBot(botUsername: string): void {
      this.event("cta_tap");
      const url = `https://t.me/${botUsername.replace(/^@/, "")}?start=join`;
      const tg = (window as any)?.Telegram?.WebApp;
      if (tg?.openTelegramLink) tg.openTelegramLink(url);
      else window.open(url, "_blank");
    },
  };
}

export type FunnelClient = ReturnType<typeof createFunnelClient>;

/** Resolve the Telegram user id from the Mini App SDK (or undefined outside Telegram). */
export function getTelegramUid(): number | undefined {
  return (window as any)?.Telegram?.WebApp?.initDataUnsafe?.user?.id;
}
