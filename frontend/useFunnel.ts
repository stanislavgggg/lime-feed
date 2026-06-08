/**
 * useFunnel.ts — React hook wrapping funnel-client.ts
 * ===================================================
 * Wires the three mini-app CRO levers into a component with minimal ceremony.
 *
 * Example — gated PicksTab with a subscribe wall and instant unlock:
 *
 *   const f = useFunnel({ baseUrl: API_BASE, botUsername: "GoalCastBot", lang: "en" });
 *
 *   useEffect(() => { f.event("cta_view"); }, []);          // CTA shown
 *
 *   return (
 *     <>
 *       {f.picks?.map((p, i) =>
 *         p.locked
 *           ? <LockedPick key={i} teaser={p.reasoning} onUnlock={f.startJoin} />
 *           : <FullPick key={i} pick={p} />
 *       )}
 *       {f.gate?.locked && <SubscribeWall channel={f.gate.channel} onJoin={f.startJoin} />}
 *     </>
 *   );
 *
 * startJoin() opens the bot's native join flow (lever #2). When the user returns to
 * the mini-app, the hook re-checks membership on window focus and unlocks instantly.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import {
  createFunnelClient,
  getTelegramUid,
  type FunnelClient,
  type GateInfo,
  type Lang,
  type Pick,
  type Stats,
} from "./funnel-client";

export interface UseFunnelOptions {
  baseUrl: string;
  botUsername: string;
  lang?: Lang;
  uid?: number; // override (defaults to Telegram SDK uid)
}

export function useFunnel(opts: UseFunnelOptions) {
  const lang = opts.lang ?? "en";
  const uid = opts.uid ?? getTelegramUid();
  const clientRef = useRef<FunnelClient>();
  if (!clientRef.current) clientRef.current = createFunnelClient({ baseUrl: opts.baseUrl, uid });
  const client = clientRef.current;

  const [picks, setPicks] = useState<Pick[] | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [gate, setGate] = useState<GateInfo | null>(null);
  const [member, setMember] = useState<boolean>(false);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await client.picks(lang);
      setPicks(res.picks);
      setStats(res.stats);
      setGate(res.gate);
      setMember(res.gate.is_member);
    } finally {
      setLoading(false);
    }
  }, [client, lang]);

  const checkMembership = useCallback(async () => {
    if (!uid) return false;
    try {
      const { member: m } = await client.membership();
      setMember(m);
      if (m) await refresh(); // unlock the gated picks
      return m;
    } catch {
      return false;
    }
  }, [client, uid, refresh]);

  // Route conversion through the bot (lever #2)
  const startJoin = useCallback(() => {
    client.openJoinViaBot(opts.botUsername);
  }, [client, opts.botUsername]);

  // Initial load
  useEffect(() => { refresh(); }, [refresh]);

  // Re-check membership when the user returns from the channel/bot → instant unlock
  useEffect(() => {
    if (!gate?.enabled || member) return;
    const onFocus = () => { checkMembership(); };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => {
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, [gate?.enabled, member, checkMembership]);

  return {
    picks, stats, gate, member, loading,
    refresh, checkMembership, startJoin,
    event: client.event.bind(client),
  };
}
