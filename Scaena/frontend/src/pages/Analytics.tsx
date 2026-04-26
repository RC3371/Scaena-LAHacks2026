import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Terminal, Check, X, RefreshCw } from "lucide-react";
import { client } from "../api/client";
import { useWebSocket } from "../hooks/useWebSocket";
import type { Insight } from "../types";
import { loadPageState, savePageState } from "../utils/pagePersistence";

interface ProposedChange {
  id: string;
  field: string;
  label: string;
  current: string;
  proposed: string;
  reason: string;
}

function parseInsightList(value?: string) {
  if (!value) return "";
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) return parsed.join(", ");
  } catch {}
  return value;
}

export function Analytics() {
  const [thoughts, setThoughts] = useState<string[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [chatIntel, setChatIntel] = useState<any>(null);
  const [entertainerId, setEntertainerId] = useState("");
  const [autoMode, setAutoMode] = useState(true);
  const [proposedChanges, setProposedChanges] = useState<ProposedChange[]>([]);
  const [approvedIds, setApprovedIds] = useState<Set<string>>(new Set());
  const [deniedIds, setDeniedIds] = useState<Set<string>>(new Set());
  const { events } = useWebSocket();

  const loadAnalytics = async (id: string, ent: any) => {
    const ingest = await client.analytics.autoIngestChatHistory(id).catch(() => null);
    const [insightData, summaryData] = await Promise.all([
      client.analytics.insights(id),
      client.analytics.summary(id),
    ]);
    setChatIntel(ingest);
    setInsights(insightData);
    setSummary(summaryData);

    const latest = insightData[0];
    const autoThoughts = [
      `> AUTO-INGESTED ${ingest?.messages_scanned ?? 0} CHAT MESSAGES`,
      `> SCANNED ${ingest?.conversations_scanned ?? 0} OUTREACH THREADS`,
      `> RECIPIENT MESSAGES :: ${ingest?.inbound_messages ?? 0}`,
      `> SOURCE :: GMAIL + OUTREACH COMMS LOG`,
    ];

    if (latest) {
      const bestVenues = parseInsightList(latest.best_venue_types) || "TBD";
      const avoid = parseInsightList(latest.avoid_segments) || "NONE";
      setThoughts([
        ...autoThoughts,
        `> LOADED ${insightData.length} INSIGHT ROUNDS`,
        `> BEST VENUE TYPE :: ${bestVenues}`,
        `> OPTIMAL PRICE :: $${latest.optimal_price || 0}/SHOW`,
        `> BEST ANGLE :: ${(latest.best_pitch_angle || "").substring(0, 40).toUpperCase()}`,
        `> AVOID :: ${avoid.toUpperCase()}`,
      ]);

      const changes: ProposedChange[] = [];
      if (latest.optimal_price && ent.current_rate && Math.abs(latest.optimal_price - ent.current_rate) > 25) {
        changes.push({
          id: "rate",
          field: "current_rate",
          label: "Minimum Rate",
          current: `$${ent.current_rate}/show`,
          proposed: `$${latest.optimal_price}/show`,
          reason: "Based on accepted booking prices and negotiation data from chat history.",
        });
      }
      const bestVenueValue = parseInsightList(latest.best_venue_types);
      if (bestVenueValue && ent.genre && !ent.genre.toLowerCase().includes(bestVenueValue.toLowerCase())) {
        changes.push({
          id: "focus",
          field: "genre",
          label: "Target Focus",
          current: ent.genre,
          proposed: `${ent.genre}, ${bestVenueValue}`,
          reason: `${bestVenueValue} conversations are showing the strongest response signal.`,
        });
      }
      if (latest.best_pitch_angle) {
        changes.push({
          id: "pitch",
          field: "highlights",
          label: "Pitch Strategy",
          current: "General approach",
          proposed: latest.best_pitch_angle,
          reason: "Agent 3 detected this pattern from Outreach/Gmail thread history.",
        });
      }
      setProposedChanges(changes);
    } else {
      setThoughts([
        ...autoThoughts,
        "> WATCHING OUTREACH/GMAIL HISTORY AUTOMATICALLY",
        "> INSIGHTS WILL APPEAR AS REAL THREADS ACCUMULATE",
      ]);
      setProposedChanges([]);
    }
  };

  useEffect(() => {
    (async () => {
      const entertainers = await client.entertainers.active();
      if (!entertainers.length) return;
      const ent = entertainers[0];
      const saved = loadPageState(`scaena.ui.analytics.${ent.id}`, {
        autoMode: true,
        thoughts: [] as string[],
        approvedIds: [] as string[],
        deniedIds: [] as string[],
      });
      setEntertainerId(ent.id);
      setAutoMode(saved.autoMode);
      setApprovedIds(new Set(saved.approvedIds || []));
      setDeniedIds(new Set(saved.deniedIds || []));
      await loadAnalytics(ent.id, ent);
    })();
  }, []);

  useEffect(() => {
    if (!entertainerId) return;
    savePageState(`scaena.ui.analytics.${entertainerId}`, {
      autoMode,
      thoughts,
      approvedIds: Array.from(approvedIds),
      deniedIds: Array.from(deniedIds),
    });
  }, [autoMode, thoughts, approvedIds, deniedIds, entertainerId]);

  useEffect(() => {
    const thinkingEvents = events.filter(
      (e) => e.agent_id === "agent3" && (e.event_type === "thinking" || e.event_type === "insight")
    );
    if (thinkingEvents.length) {
      const newThoughts = thinkingEvents.slice(0, 3).map((e) => `> ${e.message.toUpperCase()}`);
      setThoughts((prev) => [...newThoughts, ...prev].slice(0, 25));
    }
  }, [events]);

  const handleApprove = async (change: ProposedChange) => {
    setApprovedIds((prev) => new Set([...prev, change.id]));
    if (entertainerId) {
      await client.entertainers.update(entertainerId, { [change.field]: change.proposed });
    }
  };

  const handleDeny = (id: string) => {
    setDeniedIds((prev) => new Set([...prev, id]));
  };

  useEffect(() => {
    if (!autoMode || !entertainerId) return;
    const timer = window.setInterval(async () => {
      const entertainers = await client.entertainers.active();
      const ent = entertainers.find((item) => item.id === entertainerId) || entertainers[0];
      if (ent) await loadAnalytics(entertainerId, ent);
    }, 30000);
    return () => window.clearInterval(timer);
  }, [autoMode, entertainerId]);

  const latestInsight = insights[0];
  const pendingChanges = proposedChanges.filter((c) => !approvedIds.has(c.id) && !deniedIds.has(c.id));

  return (
    <div className="flex flex-col h-full overflow-hidden pr-2 pb-2">
      {/* Header */}
      <div className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-5 shadow-[6px_6px_0px_0px_var(--color-neon-green)] flex justify-between items-center shrink-0 mb-4">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-[var(--font-bungee)] text-white bg-black px-6 py-2 rounded-full border-4 border-[var(--color-neon-green)] uppercase tracking-wider">AGENT 3 :: ANALYTICS CORE</h1>
          {summary && (
            <div className="flex gap-3 font-[var(--font-space)]">
              <div className="bg-black border-2 border-[var(--color-neon-green)] px-3 py-1.5 rounded-full">
                <span className="text-[var(--color-neon-green)] font-bold text-[12px]">{summary.total_pitches} PITCHES</span>
              </div>
              <div className="bg-black border-2 border-[var(--color-neon-green)] px-3 py-1.5 rounded-full">
                <span className="text-[var(--color-neon-green)] font-bold text-[12px]">{Math.min(100, Math.round((summary.response_rate || 0) * 100))}% RESPONSE</span>
              </div>
            </div>
          )}
        </div>
        {/* Auto/Manual toggle */}
        <div className="flex items-center bg-black p-2 rounded-xl border-4 border-black gap-2 font-[var(--font-space)]">
          <button
            onClick={() => setAutoMode(false)}
            className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all border-2 ${!autoMode ? "bg-[var(--color-neon-green)] text-black border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "border-transparent text-zinc-400 hover:text-white"}`}
          >
            MANUAL
          </button>
          <button
            onClick={() => setAutoMode(true)}
            className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all border-2 ${autoMode ? "bg-white text-black border-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "border-transparent text-zinc-400 hover:text-white"}`}
          >
            AUTO ANALYZE {autoMode ? "[ON]" : ""}
          </button>
        </div>
      </div>

      {/* Split View */}
      <div className="flex flex-1 overflow-hidden gap-4 pr-2 pb-2 min-h-0">
        {/* Left: LOGIC STREAM */}
        <div className="w-72 shrink-0 bg-black border-4 border-black rounded-2xl p-5 flex flex-col shadow-[6px_6px_0px_0px_var(--color-neon-green)]">
          <div className="flex items-center gap-3 mb-5 bg-[var(--color-neon-green)] p-2 rounded-xl border-2 border-black w-fit">
            <Terminal size={18} className="text-black" strokeWidth={3} />
            <h2 className="text-[13px] font-[var(--font-bungee)] text-black">LOGIC STREAM</h2>
          </div>
          <div className="flex-1 overflow-auto pr-1 font-[var(--font-space)]">
            <div className="relative pt-2 min-h-full">
              <div className="absolute left-[10px] top-4 bottom-10 w-[3px] bg-[var(--color-neon-green)] opacity-30" />
              <div className="space-y-5 relative z-10">
                <AnimatePresence>
                  {thoughts.map((thought, i) => (
                    <motion.div
                      key={`${i}-${thought}`}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="relative pl-7"
                    >
                      <div className="absolute left-0 top-1.5 w-5 h-5 rounded-full bg-black border-3 border-[var(--color-neon-green)] z-10" style={{ border: "3px solid var(--color-neon-green)" }} />
                      <div className="text-[11px] font-bold text-[var(--color-neon-green)] uppercase leading-relaxed bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-green)] p-2.5 rounded-xl">
                        {thought}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {autoMode && thoughts.length > 0 && (
                  <div className="relative pl-7 pt-1">
                    <div className="absolute left-0 top-2 w-5 h-5 rounded-full bg-[var(--color-neon-green)] animate-ping" style={{ border: "3px solid transparent" }} />
                    <div className="absolute left-0 top-2 w-5 h-5 rounded-full bg-black" style={{ border: "3px solid var(--color-neon-green)" }} />
                    <div className="text-[11px] font-bold text-[var(--color-neon-green)] uppercase bg-black border border-dashed border-[var(--color-neon-green)] px-2.5 py-1.5 rounded-lg w-fit">LISTENING...</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right: EXTRACTED INTEL + PROPOSED CHANGES */}
        <div className="flex-1 bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl overflow-auto shadow-[6px_6px_0px_0px_var(--color-neon-green)] font-sans">
          <div className="p-7">
            <h2 className="text-2xl font-[var(--font-bungee)] text-[var(--color-neon-green)] mb-7 bg-black px-6 py-2 rounded-full border-2 border-[var(--color-neon-green)] inline-block">EXTRACTED INTEL</h2>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              {[
                ["THREADS", chatIntel?.conversations_scanned ?? 0],
                ["MESSAGES", chatIntel?.messages_scanned ?? 0],
                ["RECIPIENT", chatIntel?.inbound_messages ?? 0],
                ["TEAM", chatIntel?.outbound_messages ?? 0],
              ].map(([label, value]) => (
                <div key={label} className="bg-black border-2 border-[var(--color-neon-green)] rounded-xl p-3">
                  <p className="text-[10px] font-[var(--font-space)] text-zinc-500 font-bold uppercase">{label}</p>
                  <p className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-green)]">{value}</p>
                </div>
              ))}
            </div>

            {latestInsight ? (
              <div className="space-y-5">
                {/* Positive Signals */}
                <div className="bg-black border-4 border-black rounded-2xl p-5 shadow-[4px_4px_0px_0px_var(--color-neon-green)]">
                  <h3 className="text-[14px] font-[var(--font-bungee)] text-black bg-[var(--color-neon-green)] px-4 py-2 rounded-xl mb-5 inline-flex items-center gap-2 border-2 border-black">
                    <div className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" /> POSITIVE SIGNALS
                  </h3>
                  <div className="space-y-4">
                    <div className="flex items-start gap-3">
                      <div className="w-2.5 h-2.5 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0" />
                      <p className="text-[15px] text-zinc-100 leading-relaxed">
                        Best venue type: <span className="text-[var(--color-neon-green)] font-[var(--font-bungee)] text-xl mx-1">{parseInsightList(latestInsight.best_venue_types)}</span>
                      </p>
                    </div>
                    <div className="flex items-start gap-3">
                      <div className="w-2.5 h-2.5 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0" />
                      <p className="text-[15px] text-zinc-100 leading-relaxed">
                        Optimal angle: <span className="text-[var(--color-neon-green)] font-semibold">{latestInsight.best_pitch_angle}</span>
                      </p>
                    </div>
                    {latestInsight.optimal_price > 0 && (
                      <div className="flex items-start gap-3">
                        <div className="w-2.5 h-2.5 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0" />
                        <p className="text-[15px] text-zinc-100 leading-relaxed">
                          Sweet spot: <span className="text-[var(--color-neon-green)] font-[var(--font-bungee)] text-xl mx-1">${latestInsight.optimal_price}/show</span>
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Avoid */}
                {latestInsight.avoid_segments && (
                  <div className="bg-black border-4 border-black rounded-2xl p-5 shadow-[4px_4px_0px_0px_var(--color-neon-green)]">
                    <h3 className="text-[14px] font-[var(--font-bungee)] text-black bg-[var(--color-neon-green)] px-4 py-2 rounded-xl mb-5 inline-flex items-center gap-2 border-2 border-black">
                      <div className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" /> NEGATIVE FRICTION
                    </h3>
                    <div className="flex items-start gap-3">
                      <div className="w-2.5 h-2.5 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0" />
                      <p className="text-[15px] text-zinc-100 leading-relaxed">Avoid: <span className="text-[var(--color-neon-green)] font-semibold">{parseInsightList(latestInsight.avoid_segments)}</span></p>
                    </div>
                  </div>
                )}

                {latestInsight.insights_narrative && (
                  <div className="bg-black border-2 border-zinc-800 rounded-xl p-4">
                    <p className="text-[12px] font-bold text-zinc-500 font-[var(--font-space)] uppercase mb-2">ROUND {latestInsight.round_number} NARRATIVE</p>
                    <p className="text-[13px] text-zinc-300 leading-relaxed">{latestInsight.insights_narrative}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-[14px] font-bold font-[var(--font-space)] text-[var(--color-neon-green)] mt-4 uppercase bg-black p-5 rounded-xl border-2 border-dashed border-[var(--color-neon-green)]">
                AGENT 3 IS READING OUTREACH/GMAIL CHAT HISTORY AUTOMATICALLY.<br />
                <span className="text-zinc-600 text-[12px] mt-1 block">NO MANUAL REPLY LOGGING REQUIRED.</span>
              </div>
            )}

            {/* Proposed Changes */}
            {proposedChanges.length > 0 && (
              <div className="mt-8">
                <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-green)] mb-5 bg-black px-5 py-2 rounded-full border-2 border-[var(--color-neon-green)] inline-flex items-center gap-2">
                  <RefreshCw size={18} strokeWidth={3} /> PROPOSED CHANGES
                </h2>
                <div className="space-y-3">
                  {proposedChanges.map((change) => {
                    const approved = approvedIds.has(change.id);
                    const denied = deniedIds.has(change.id);
                    return (
                      <motion.div
                        key={change.id}
                        layout
                        className={`bg-black border-4 rounded-2xl p-5 transition-all ${
                          approved ? "border-[var(--color-neon-green)] opacity-60" :
                          denied ? "border-zinc-700 opacity-40" :
                          "border-[var(--color-neon-green)] shadow-[4px_4px_0px_0px_var(--color-neon-green)]"
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1 min-w-0">
                            <p className="text-[12px] font-bold text-[var(--color-neon-green)] font-[var(--font-space)] uppercase mb-2">{change.label}</p>
                            <div className="flex items-center gap-3 flex-wrap">
                              <span className="text-[13px] text-zinc-500 line-through">{change.current}</span>
                              <span className="text-zinc-500">→</span>
                              <span className="text-[14px] font-bold text-white">{change.proposed}</span>
                            </div>
                            <p className="text-[12px] text-zinc-500 mt-2 italic">{change.reason}</p>
                          </div>
                          {!approved && !denied && (
                            <div className="flex gap-2 ml-4 shrink-0">
                              <button
                                onClick={() => handleApprove(change)}
                                className="flex items-center gap-1 px-4 py-2 bg-[var(--color-neon-green)] text-black border-2 border-black text-[12px] font-bold rounded-lg hover:-translate-y-0.5 transition-all font-[var(--font-space)]"
                              >
                                <Check size={14} strokeWidth={3} /> APPROVE
                              </button>
                              <button
                                onClick={() => handleDeny(change.id)}
                                className="flex items-center gap-1 px-4 py-2 bg-zinc-800 text-zinc-300 border-2 border-zinc-600 text-[12px] font-bold rounded-lg hover:bg-zinc-700 transition-all font-[var(--font-space)]"
                              >
                                <X size={14} strokeWidth={3} /> DENY
                              </button>
                            </div>
                          )}
                          {approved && <span className="text-[12px] font-bold text-[var(--color-neon-green)] font-[var(--font-space)] ml-4">✓ APPLIED</span>}
                          {denied && <span className="text-[12px] font-bold text-zinc-600 font-[var(--font-space)] ml-4">✗ DENIED</span>}
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Refresh button */}
            <div className="mt-8 pt-6 border-t-4 border-black">
              <button
                onClick={async () => {
                  if (!entertainerId) return;
                  const entertainers = await client.entertainers.active();
                  const ent = entertainers.find((item) => item.id === entertainerId) || entertainers[0];
                  if (ent) await loadAnalytics(entertainerId, ent);
                }}
                className="px-6 py-3 bg-[var(--color-neon-green)] text-black border-4 border-black font-[var(--font-bungee)] rounded-xl hover:bg-white hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all text-[15px]"
              >
                REFRESH INTEL
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
