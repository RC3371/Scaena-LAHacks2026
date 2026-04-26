import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Search, Terminal, ChevronDown, Send, Zap, TrendingUp } from "lucide-react";
import { client } from "../api/client";
import { useWebSocket } from "../hooks/useWebSocket";
import type { Venue } from "../types";


export function MarketInsights() {
  const [isScanning, setIsScanning] = useState(false);
  const [autoMode, setAutoMode] = useState(true);
  const [logs, setLogs] = useState<string[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [input, setInput] = useState("");
  const [entertainerId, setEntertainerId] = useState("");
  const [summary, setSummary] = useState<any>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [sentToOutreach, setSentToOutreach] = useState<Set<string>>(new Set());
  const [sendingId, setSendingId] = useState<string | null>(null);
  const { events } = useWebSocket();

  useEffect(() => {
    (async () => {
      const entertainers = await client.entertainers.active();
      if (!entertainers.length) return;
      const ent = entertainers[0];
      setEntertainerId(ent.id);
      setAutoMode(ent.outreach_mode !== "manual_approve");
      const [venueData, summaryData] = await Promise.all([
        client.venues.list(ent.id),
        client.analytics.summary(ent.id),
      ]);
      setVenues(venueData);
      setSummary(summaryData);
      setLogs([
        `> PROFILE LOADED :: ${ent.name.toUpperCase()}`,
        `> LOADED ${venueData.length} VENUES FROM LAST SCAN`,
        "> AGENT 1 READY :: AWAITING DIRECTIVE",
      ]);
    })();
  }, []);

  useEffect(() => {
    const agentEvents = events.filter((e) => e.agent_id === "agent1");
    if (agentEvents.length) {
      setLogs((prev) => {
        const newLogs = agentEvents.slice(0, 3).map((e) => `> ${e.message.toUpperCase()}`);
        return [...newLogs, ...prev].slice(0, 25);
      });
    }
  }, [events]);

  const handleUpdateDirective = async () => {
    if (!entertainerId) return;
    setIsScanning(true);
    setLogs((prev) => [`> DIRECTIVE UPDATED :: "${input || "GENERAL SCAN"}"`, ...prev]);
    try {
      await client.outreach.researchRefinement({
        entertainer_id: entertainerId,
        user_instruction: input || "Scan all venue types",
      });
      setLogs((prev) => ["> REFINEMENT SENT :: AGENT 1 PROCESSING", ...prev]);
      setTimeout(async () => {
        const venueData = await client.venues.list(entertainerId);
        const summaryData = await client.analytics.summary(entertainerId);
        setVenues(venueData);
        setSummary(summaryData);
        setLogs((prev) => [`> SCAN COMPLETE :: ${venueData.length} VENUES FOUND`, ...prev]);
        setIsScanning(false);
      }, 3000);
    } catch {
      setLogs((prev) => ["> ERROR :: COULD NOT REACH AGENT 1", ...prev]);
      setIsScanning(false);
    }
    setInput("");
  };

  const handleSendToOutreach = async (venue: Venue) => {
    if (!entertainerId || sendingId) return;
    setSendingId(venue.id);
    try {
      const generated = await client.outreach.generatePitch({
        entertainer_id: entertainerId,
        venue_id: venue.id,
        recipient_email: venue.contact_email || undefined,
        venue_contact_approach: venue.contact_approach || undefined,
        status: "draft",
      });
      if (autoMode && generated.pitch_id) {
        await client.gmail.sendPitch(generated.pitch_id);
      }
      setSentToOutreach((prev) => new Set([...prev, venue.id]));
      setLogs((prev) => [
        autoMode
          ? `> AUTO SENT :: ${venue.name.toUpperCase()} -> GMAIL`
          : `> GENERATED ${String(generated.generation_source || "DRAFT").toUpperCase()} PITCH :: ${venue.name.toUpperCase()}`,
        ...prev,
      ]);
    } catch (error) {
      console.error(error);
      setLogs((prev) => ["> ERROR :: COULD NOT GENERATE OR SEND PITCH", ...prev]);
    }
    setSendingId(null);
  };

  const sortedVenues = [...venues].sort((a, b) => (b.fit_score ?? 0) - (a.fit_score ?? 0));

  return (
    <div className="flex flex-col h-full overflow-hidden pr-2 pb-2">
      {/* Header */}
      <div className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-5 flex flex-col gap-4 shadow-[6px_6px_0px_0px_var(--color-neon-pink)] mb-4 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 bg-black border-4 border-[var(--color-neon-pink)] w-fit px-6 py-2 rounded-full">
            <div className={`w-3 h-3 rounded-full bg-[var(--color-neon-pink)] ${isScanning ? "animate-ping" : ""}`} />
            <h1 className="text-xl font-[var(--font-bungee)] text-white tracking-wider uppercase">
              {isScanning ? "AGENT 1 :: SCANNING..." : "AGENT 1 :: STANDBY"}
            </h1>
          </div>
          {/* Automation toggle */}
          <div className="flex items-center bg-black p-2 rounded-xl border-4 border-black gap-2 font-[var(--font-space)]">
            <button
              onClick={() => setAutoMode(false)}
              className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all border-2 ${!autoMode ? "bg-[var(--color-neon-pink)] text-black border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "border-transparent text-zinc-400 hover:text-white"}`}
            >
              MANUAL QUEUE
            </button>
            <button
              onClick={() => setAutoMode(true)}
              className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all border-2 flex items-center gap-2 ${autoMode ? "bg-white text-black border-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "border-transparent text-zinc-400 hover:text-white"}`}
            >
              <Zap size={14} strokeWidth={3} /> AUTO OUTREACH
            </button>
          </div>
        </div>

        {/* Market Objective input */}
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-neon-pink)]" size={20} strokeWidth={3} />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Market objective: e.g. focus on college campuses, music festivals, music shows, and bars..."
              className="w-full bg-black border-4 border-black rounded-full pl-12 pr-4 py-3 text-[15px] text-white placeholder-[var(--color-neon-pink)]/40 focus:outline-none focus:border-[var(--color-neon-pink)] transition-all font-sans"
              onKeyDown={(e) => e.key === "Enter" && handleUpdateDirective()}
            />
          </div>
          <button
            onClick={handleUpdateDirective}
            disabled={isScanning}
            className="px-6 py-3 bg-[var(--color-neon-pink)] text-black border-4 border-black text-[14px] font-bold rounded-full hover:bg-white hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all uppercase whitespace-nowrap disabled:opacity-50 disabled:pointer-events-none font-[var(--font-space)]"
          >
            UPDATE REQUIREMENTS
          </button>
        </div>
      </div>

      {/* Market Research Summary */}
      {summary && (
        <div className="grid grid-cols-4 gap-3 mb-4 shrink-0">
          {[
            { label: "PITCHES SENT", value: summary.total_pitches, color: "var(--color-neon-pink)" },
            { label: "RESPONSE RATE", value: `${Math.min(100, Math.round((summary.response_rate || 0) * 100))}%`, color: "var(--color-neon-pink)" },
            { label: "AVG RATE", value: `$${Math.round(summary.price_data?.avg_proposed || 0)}`, color: "var(--color-neon-pink)" },
            { label: "VENUES FOUND", value: venues.length, color: "var(--color-neon-pink)" },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-[var(--color-panel-bg)] border-4 border-black rounded-xl p-4 flex flex-col gap-1 shadow-[3px_3px_0px_0px_var(--color-neon-pink)]">
              <span className="text-[11px] font-bold text-zinc-500 font-[var(--font-space)] uppercase tracking-widest">{label}</span>
              <span className="text-2xl font-[var(--font-bungee)]" style={{ color }}>{value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Split View */}
      <div className="flex flex-1 overflow-hidden gap-4 pr-2 pb-2 min-h-0">
        {/* Left: SYS LOG */}
        <div className="w-52 shrink-0 border-4 border-black bg-black rounded-2xl p-4 flex flex-col shadow-[6px_6px_0px_0px_var(--color-neon-pink)]">
          <div className="flex items-center gap-3 mb-4 bg-[var(--color-panel-bg)] p-2 rounded-xl border-2 border-[var(--color-neon-pink)] w-fit">
            <Terminal size={18} className="text-[var(--color-neon-pink)]" strokeWidth={3} />
            <h2 className="text-[13px] font-[var(--font-bungee)] text-[var(--color-neon-pink)]">SYS LOG</h2>
          </div>
          <div className="flex-1 overflow-auto space-y-2 pr-1 font-[var(--font-space)]">
            <AnimatePresence>
              {logs.map((log, i) => (
                <motion.div
                  key={`${i}-${log}`}
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-[11px] text-[var(--color-neon-pink)] uppercase font-bold leading-relaxed bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-pink)] p-2 rounded-lg"
                  style={{ textShadow: "0 0 4px var(--color-neon-pink)" }}
                >
                  {log}
                </motion.div>
              ))}
            </AnimatePresence>
            {isScanning && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-[var(--color-neon-pink)] text-[13px] font-bold bg-black border-2 border-[var(--color-neon-pink)] p-2 rounded w-fit"
              >
                <span className="animate-pulse">_</span>PROCESSING
              </motion.div>
            )}
          </div>
        </div>

        {/* Right: MATCH FEED */}
        <div className="flex-1 overflow-auto bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-5 shadow-[6px_6px_0px_0px_var(--color-neon-pink)]">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-pink)] bg-black inline-block px-4 py-2 border-2 border-[var(--color-neon-pink)] rounded-full">
              MATCH FEED
            </h2>
            <span className="text-[12px] font-bold text-zinc-500 font-[var(--font-space)]">{sortedVenues.length} VENUES</span>
          </div>

          <div className="space-y-3">
            <AnimatePresence>
              {sortedVenues.map((venue, i) => {
                const raw = venue.fit_score ?? 0.5;
                const score = raw > 1 ? Math.round(raw) : Math.round(raw * 100);
                const isExpanded = expandedId === venue.id;
                const isSent = sentToOutreach.has(venue.id);

                return (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2, delay: i * 0.03 }}
                    key={venue.id}
                    className="bg-black border-4 border-black rounded-2xl overflow-hidden hover:border-[var(--color-neon-pink)] transition-colors"
                  >
                    {/* Card Header - always visible, clickable */}
                    <button
                      className="w-full flex items-center justify-between p-4 text-left"
                      onClick={() => setExpandedId(isExpanded ? null : venue.id)}
                    >
                      <div className="flex items-center gap-4 flex-1 min-w-0">
                        <div>
                          <h3 className="text-[16px] font-[var(--font-bungee)] text-white tracking-widest">{venue.name.toUpperCase()}</h3>
                          <p className="text-[12px] text-zinc-400 mt-0.5 font-sans">
                            <span className="text-white font-semibold">{venue.venue_type || "Venue"}</span>
                            {venue.typical_pay && <span className="ml-2 text-[var(--color-neon-pink)]">// {venue.typical_pay}</span>}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 shrink-0">
                        {/* Score bar */}
                        <div className="flex flex-col items-end gap-1 w-28">
                          <div className="flex justify-between w-full">
                            <span className="text-[11px] font-bold text-zinc-500 font-[var(--font-space)]">MATCH</span>
                            <span className="text-[15px] font-[var(--font-bungee)] text-[var(--color-neon-pink)]">{score}%</span>
                          </div>
                          <div className="w-full h-2 rounded-full bg-zinc-800 overflow-hidden">
                            <div
                              className="h-full bg-[var(--color-neon-pink)] rounded-full"
                              style={{ width: `${score}%`, opacity: score < 50 ? 0.4 : score < 75 ? 0.7 : 1 }}
                            />
                          </div>
                        </div>
                        <ChevronDown
                          size={18}
                          strokeWidth={3}
                          className={`text-zinc-500 transition-transform ${isExpanded ? "rotate-180" : ""}`}
                        />
                      </div>
                    </button>

                    {/* Expanded Content */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden"
                        >
                          <div className="border-t-4 border-[var(--color-panel-bg)]">
                            <div className="p-5 space-y-4">
                              {/* Info grid */}
                              <div className="grid grid-cols-2 gap-3">
                                {venue.typical_pay && (
                                  <div className="bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-pink)]/30 rounded-xl p-3">
                                    <p className="text-[11px] font-bold text-zinc-500 font-[var(--font-space)] uppercase mb-1">Historical Pricing</p>
                                    <p className="text-[14px] font-bold text-white">{venue.typical_pay}</p>
                                  </div>
                                )}
                                {venue.contact_approach && (
                                  <div className="bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-pink)]/30 rounded-xl p-3">
                                    <p className="text-[11px] font-bold text-zinc-500 font-[var(--font-space)] uppercase mb-1">Best Approach</p>
                                    <p className="text-[14px] font-bold text-white">{venue.contact_approach}</p>
                                  </div>
                                )}
                                {venue.contact_email && (
                                  <div className="bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-pink)]/30 rounded-xl p-3">
                                    <p className="text-[11px] font-bold text-zinc-500 font-[var(--font-space)] uppercase mb-1">Contact Email</p>
                                    <p className="text-[14px] font-bold text-white break-all">{venue.contact_email}</p>
                                  </div>
                                )}
                              </div>

                              {venue.why_fits && (
                                <div className="bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-pink)]/30 rounded-xl p-3">
                                  <p className="text-[11px] font-bold text-zinc-500 font-[var(--font-space)] uppercase mb-1 flex items-center gap-1">
                                    <TrendingUp size={11} /> Why It Fits
                                  </p>
                                  <p className="text-[13px] text-zinc-200 leading-relaxed">{venue.why_fits}</p>
                                </div>
                              )}

                              {/* Send to Outreach */}
                              <div className="flex justify-end pt-2">
                                {isSent ? (
                                  <div className="flex items-center gap-2 px-5 py-2.5 bg-[var(--color-neon-pink)]/20 border-2 border-[var(--color-neon-pink)] rounded-full text-[var(--color-neon-pink)] font-bold text-[13px] font-[var(--font-space)]">
                                    ✓ QUEUED IN OUTREACH
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => handleSendToOutreach(venue)}
                                    disabled={sendingId === venue.id}
                                    className="flex items-center gap-2 px-5 py-2.5 bg-[var(--color-neon-pink)] text-black border-4 border-black font-bold text-[13px] rounded-full hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] transition-all font-[var(--font-space)] uppercase disabled:opacity-50"
                                  >
                                    <Send size={14} strokeWidth={3} />
                                    {sendingId === venue.id ? "SENDING..." : "SEND TO OUTREACH"}
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </motion.div>
                );
              })}
            </AnimatePresence>

            {venues.length === 0 && !isScanning && (
              <div className="text-[15px] font-bold font-[var(--font-space)] text-[var(--color-neon-pink)] mt-10 text-center uppercase bg-black p-4 rounded-xl border-2 border-dashed border-[var(--color-neon-pink)]">
                AWAITING DIRECTIVE
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
