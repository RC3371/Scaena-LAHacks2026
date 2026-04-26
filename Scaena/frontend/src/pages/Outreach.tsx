import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Send, MessageSquare, CheckCircle2, RefreshCw, Edit3, Mail, Link2 } from "lucide-react";
import { client } from "../api/client";
import { CollapsibleText } from "../components/CollapsibleText";
import { useWebSocket } from "../hooks/useWebSocket";
import type { Conversation, Pitch } from "../types";

function Typewriter({ text, onComplete }: { text: string; onComplete?: () => void }) {
  const [displayed, setDisplayed] = useState("");
  useEffect(() => {
    setDisplayed("");
    let i = 0;
    const timer = setInterval(() => {
      setDisplayed(text.substring(0, i));
      i++;
      if (i > text.length) { clearInterval(timer); onComplete?.(); }
    }, 6);
    return () => clearInterval(timer);
  }, [text]);
  return <span>{displayed}</span>;
}

type RightTab = "comms" | "draft";
type SyncState = "idle" | "syncing" | "up_to_date" | "error";

type GmailStatus = {
  configured: boolean;
  connected: boolean;
  email?: string | null;
  live_sends: boolean;
  read_sync_enabled?: boolean;
  last_sync_at?: string | null;
};

const statusBadge: Record<string, string> = {
  draft: "bg-zinc-700 text-zinc-300",
  sent: "bg-blue-900 text-blue-300",
  interested: "bg-cyan-900 text-[var(--color-neon-cyan)]",
  negotiating: "bg-purple-900 text-purple-300",
  booked: "bg-green-900 text-[var(--color-neon-green)]",
  rejected: "bg-red-900 text-red-400",
  maybe: "bg-yellow-900 text-yellow-300",
};

export function Outreach() {
  const [pitches, setPitches] = useState<Pitch[]>([]);
  const [conversations, setConversations] = useState<Record<string, Conversation>>({});
  const [activePitchId, setActivePitchId] = useState<string | null>(null);
  const [rightTab, setRightTab] = useState<RightTab>("comms");
  const [isDrafting, setIsDrafting] = useState(false);
  const [isFinalized, setIsFinalized] = useState(false);
  const [autoMode, setAutoMode] = useState(true);
  const [strategyInput, setStrategyInput] = useState("");
  const [editingDraft, setEditingDraft] = useState(false);
  const [draftText, setDraftText] = useState("");
  const [draftEdited, setDraftEdited] = useState(false);
  const [entertainerId, setEntertainerId] = useState("");
  const [entertainerName, setEntertainerName] = useState("");
  const [gmailStatus, setGmailStatus] = useState<GmailStatus | null>(null);
  const [gmailSyncing, setGmailSyncing] = useState(false);
  const [syncState, setSyncState] = useState<SyncState>("idle");
  const [gmailNotice, setGmailNotice] = useState("");
  const syncInFlightRef = useRef(false);
  const { events } = useWebSocket();

  const loadGmailStatus = async (id: string) => {
    try {
      const status = await client.gmail.status(id);
      setGmailStatus(status);
      return status as GmailStatus;
    } catch {
      setGmailStatus(null);
      return null;
    }
  };

  useEffect(() => {
    (async () => {
      if (new URLSearchParams(window.location.search).get("gmail") === "connected") {
        setGmailNotice("Gmail connected. Reply sync is ready after reconnect grants read access.");
        window.history.replaceState({}, "", window.location.pathname);
      }
      const entertainers = await client.entertainers.active();
      if (!entertainers.length) return;
      const ent = entertainers[0];
      setEntertainerId(ent.id);
      setEntertainerName(ent.name);
      if (ent.outreach_mode !== "auto_pitch") {
        await client.entertainers.update(ent.id, { outreach_mode: "auto_pitch" });
      }
      setAutoMode(true);
      await loadGmailStatus(ent.id);
      const pitchData = await client.outreach.pitches(ent.id);
      setPitches(pitchData);
      if (pitchData.length) setActivePitchId(pitchData[0].id);
      const convMap: Record<string, Conversation> = {};
      await Promise.all(pitchData.slice(0, 12).map(async (p) => {
        try { convMap[p.id] = await client.conversations.getByPitch(p.id); } catch {}
      }));
      setConversations(convMap);
    })();
  }, []);

  // Watch for new agent2 events to refresh pitches
  useEffect(() => {
    const agent2Events = events.filter((e) => e.agent_id === "agent2");
    if (agent2Events.length && entertainerId) {
      client.outreach.pitches(entertainerId).then(setPitches);
    }
  }, [events, entertainerId]);

  const activePitch = pitches.find((p) => p.id === activePitchId);
  const activeConv = activePitchId ? conversations[activePitchId] : undefined;

  useEffect(() => {
    if (activePitch) {
      setDraftText(activePitch.pitch_body);
      setIsDrafting(true);
      setIsFinalized(false);
      setEditingDraft(false);
      setDraftEdited(false);
    }
  }, [activePitchId, activePitch?.pitch_body]);

  const refreshPitchesAndConversations = async () => {
    if (!entertainerId) return;
    const pitchData = await client.outreach.pitches(entertainerId);
    setPitches(pitchData);
    const convMap: Record<string, Conversation> = {};
    await Promise.all(pitchData.slice(0, 12).map(async (p) => {
      try { convMap[p.id] = await client.conversations.getByPitch(p.id); } catch {}
    }));
    setConversations((prev) => ({ ...prev, ...convMap }));
  };

  const handleConnectGmail = async () => {
    if (!entertainerId) return;
    try {
      const { auth_url } = await client.gmail.authUrl(entertainerId, "/outreach?gmail=connected");
      window.location.href = auth_url;
    } catch (error: any) {
      const detail = error?.response?.data?.detail || "Gmail OAuth is not configured yet.";
      window.alert(detail);
    }
  };

  const handleSyncReplies = async (silent = false) => {
    if (!entertainerId || syncInFlightRef.current) return;
    syncInFlightRef.current = true;
    setGmailSyncing(true);
    setSyncState("syncing");
    setGmailNotice("");
    try {
      const result = await client.gmail.syncReplies(entertainerId);
      await refreshPitchesAndConversations();
      await loadGmailStatus(entertainerId);
      const imported = result.replies_imported ?? 0;
      const drafts = result.reply_drafts_generated ?? 0;
      const sent = result.auto_replies_sent ?? 0;
      if (!silent || imported > 0 || drafts > 0 || sent > 0) {
        setGmailNotice(`Auto sync imported ${imported} replies, generated ${drafts} drafts, and sent ${sent}.`);
      }
      if (imported === 0 && drafts === 0 && sent === 0) {
        setGmailNotice("Up to date.");
      }
      setSyncState("up_to_date");
      setRightTab("comms");
    } catch (error: any) {
      const detail = error?.response?.data?.detail || "Gmail reply sync failed. Reconnect Gmail and try again.";
      setGmailNotice(detail);
      setSyncState("error");
      if (String(detail).toLowerCase().includes("reconnect")) {
        await loadGmailStatus(entertainerId);
      }
    } finally {
      syncInFlightRef.current = false;
      setGmailSyncing(false);
    }
  };

  useEffect(() => {
    if (!entertainerId || !gmailStatus?.connected || !gmailStatus?.read_sync_enabled) return;
    handleSyncReplies(true);
    const timer = window.setInterval(() => {
      handleSyncReplies(true);
    }, 45000);
    return () => window.clearInterval(timer);
  }, [entertainerId, gmailStatus?.connected, gmailStatus?.read_sync_enabled]);

  useEffect(() => {
    if (!gmailNotice) return;
    const timer = window.setTimeout(() => setGmailNotice(""), 5000);
    return () => window.clearTimeout(timer);
  }, [gmailNotice]);

  const handleAdjustPitch = async () => {
    if (!strategyInput.trim() || !activePitch || !entertainerId) return;
    setIsDrafting(true);
    setIsFinalized(false);
    setEditingDraft(false);
    try {
      const regenerated = await client.outreach.regeneratePitch(activePitch.id, {
        entertainer_id: entertainerId,
        strategy_instruction: strategyInput,
      });
      setDraftText(regenerated.pitch_body || "");
      const pitchData = await client.outreach.pitches(entertainerId);
      setPitches(pitchData);
      setIsDrafting(false);
    } catch {
      setIsDrafting(false);
    }
    setStrategyInput("");
  };

  const handleApprove = async () => {
    if (!activePitch) return;
    try {
      if (draftText && draftText !== activePitch.pitch_body) {
        await client.outreach.updatePitch(activePitch.id, { pitch_body: draftText });
      }
      await client.gmail.sendPitch(activePitch.id);
      const pitchData = await client.outreach.pitches(entertainerId);
      setPitches(pitchData);
      setIsFinalized(true);
      setDraftEdited(false);
    } catch (error: any) {
      const detail = error?.response?.data?.detail || "Gmail send failed. Check Gmail connection and recipient email.";
      window.alert(detail);
    }
  };

  const handleDiscard = async () => {
    if (!activePitch) return;
    try {
      await client.outreach.updatePitch(activePitch.id, { status: "rejected" });
      const pitchData = await client.outreach.pitches(entertainerId);
      setPitches(pitchData);
      setActivePitchId(pitchData.find((p) => p.id !== activePitch.id)?.id || null);
    } catch {}
  };

  const toggleMode = async (mode: "manual_approve" | "auto_pitch") => {
    const isAuto = mode === "auto_pitch";
    setAutoMode(isAuto);
    if (entertainerId) {
      await client.entertainers.update(entertainerId, { outreach_mode: mode });
    }
  };

  const currentDraft = editingDraft ? draftText : (activePitch?.pitch_body || "");
  const syncLabel = gmailSyncing || syncState === "syncing" ? "SYNCING" : syncState === "up_to_date" ? "UP TO DATE" : "AUTO SYNC";
  const SyncIcon = syncState === "up_to_date" ? CheckCircle2 : RefreshCw;

  return (
    <div className="flex flex-col h-full overflow-hidden pr-1 pb-1">
      {/* Header */}
      <div className="bg-[var(--color-panel-bg)] border-4 border-black p-3 rounded-2xl shadow-[4px_4px_0px_0px_var(--color-neon-cyan)] flex justify-between items-center gap-3 shrink-0 mb-3">
        <h1 className="text-base font-[var(--font-bungee)] text-white bg-black px-4 py-1.5 rounded-full border-4 border-[var(--color-neon-cyan)] uppercase tracking-wider">AGENT 2 :: OUTREACH</h1>
        <div className="flex items-center gap-2">
          <div className="hidden lg:flex items-center gap-2 bg-black border-2 border-[var(--color-neon-cyan)] px-2.5 py-1.5 rounded-full font-[var(--font-space)]">
            <Mail size={13} className={gmailStatus?.connected ? "text-[var(--color-neon-green)]" : "text-zinc-500"} strokeWidth={3} />
            <span className={`text-[10px] font-bold uppercase max-w-[180px] truncate ${gmailStatus?.connected ? "text-[var(--color-neon-green)]" : "text-zinc-400"}`}>
              {gmailStatus?.connected ? (gmailStatus.email || "GMAIL CONNECTED") : "GMAIL DISCONNECTED"}
            </span>
            {gmailStatus?.connected && gmailStatus.read_sync_enabled ? (
              <div
                className="flex items-center gap-1 px-2 py-0.5 bg-[var(--color-neon-cyan)] text-black rounded-full border-2 border-black text-[10px] font-bold"
              >
                <SyncIcon size={11} strokeWidth={3} className={gmailSyncing ? "animate-spin" : ""} /> {syncLabel}
              </div>
            ) : (
              <button
                onClick={handleConnectGmail}
                disabled={!gmailStatus?.configured}
                className="flex items-center gap-1 px-2 py-0.5 bg-white text-black rounded-full border-2 border-black text-[10px] font-bold disabled:opacity-50"
              >
                <Link2 size={11} strokeWidth={3} /> {gmailStatus?.connected ? "RECONNECT" : "CONNECT"}
              </button>
            )}
          </div>
          {autoMode && (
            <div className="hidden xl:flex items-center gap-2 bg-black border-2 border-[var(--color-neon-cyan)] px-2.5 py-1.5 rounded-full font-[var(--font-space)]">
              <div className="w-2 h-2 rounded-full bg-[var(--color-neon-cyan)] animate-ping" />
              <span className="text-[10px] font-bold text-[var(--color-neon-cyan)] uppercase">
                AUTO MODE ACTIVE
              </span>
            </div>
          )}
          <div className="flex items-center bg-black p-1.5 rounded-xl border-4 border-black gap-1.5 font-[var(--font-space)]">
            <button
              onClick={() => toggleMode("manual_approve")}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all border-2 ${!autoMode ? "bg-[var(--color-neon-cyan)] text-black border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "border-transparent text-zinc-400 hover:text-white"}`}
            >
              MANUAL APPROVAL
            </button>
            <button
              onClick={() => toggleMode("auto_pitch")}
              className={`px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all border-2 ${autoMode ? "bg-white text-black border-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "border-transparent text-zinc-400 hover:text-white"}`}
            >
              AUTO PITCH {autoMode ? "[ACTIVE]" : ""}
            </button>
          </div>
        </div>
      </div>

      {/* Split View */}
      <div className="flex flex-1 overflow-hidden gap-3 pr-1 pb-1 min-h-0">
        {/* Left: Contact List */}
        <div className="w-64 shrink-0 border-4 border-black bg-[var(--color-panel-bg)] rounded-2xl p-3 overflow-y-auto shadow-[4px_4px_0px_0px_var(--color-neon-cyan)]">
          <h2 className="text-[12px] font-[var(--font-bungee)] text-[var(--color-neon-cyan)] mb-3 bg-black px-3 py-1 rounded-full border-2 border-[var(--color-neon-cyan)] inline-block">
            CONTACTS ({pitches.length})
          </h2>
          <div className="space-y-2 font-sans">
            {pitches.map((pitch) => (
              <button
                key={pitch.id}
                onClick={() => { setActivePitchId(pitch.id); setIsFinalized(false); }}
                className={`w-full text-left px-3 py-2.5 rounded-xl border-4 transition-all duration-150 ${
                  activePitchId === pitch.id
                    ? "bg-[var(--color-neon-cyan)] text-black border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] -translate-y-0.5"
                    : "bg-black text-white border-black hover:border-[var(--color-neon-cyan)]"
                }`}
              >
                <div className="flex justify-between items-start">
                  <p className={`text-[13px] font-bold leading-tight ${activePitchId === pitch.id ? "text-black" : "text-white"}`}>
                    {pitch.venue_name}
                  </p>
                  <MessageSquare size={14} className={activePitchId === pitch.id ? "text-black shrink-0 mt-0.5" : "text-[var(--color-neon-cyan)] shrink-0 mt-0.5"} />
                </div>
                <p className={`mt-1.5 text-[10px] font-bold font-[var(--font-space)] leading-tight break-all ${activePitchId === pitch.id ? "text-black/80" : "text-zinc-400"}`}>
                  {pitch.recipient_email || "NO TARGET EMAIL"}
                </p>
                <div className="flex justify-between items-center mt-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase font-[var(--font-space)] ${activePitchId === pitch.id ? "bg-black text-[var(--color-neon-cyan)]" : (statusBadge[pitch.status] || "bg-zinc-800 text-zinc-400")}`}>
                    {pitch.status}
                  </span>
                  {pitch.followup_count > 0 && (
                    <span className={`text-[10px] font-bold font-[var(--font-space)] ${activePitchId === pitch.id ? "text-black" : "text-zinc-500"}`}>
                      {pitch.followup_count} FU
                    </span>
                  )}
                </div>
              </button>
            ))}
            {pitches.length === 0 && (
              <p className="text-zinc-600 text-[12px] font-[var(--font-space)] uppercase p-2">NO CONTACTS YET.<br />SEND VENUES FROM MARKET SCAN.</p>
            )}
          </div>
        </div>

        {/* Right: Workspace */}
        <div className="relative flex-1 flex flex-col min-h-0 min-w-0">
          {activePitch ? (
            <>
              {/* Tab switcher */}
              <div className="flex gap-1 mb-3 bg-black border-4 border-black rounded-xl p-1 w-fit font-[var(--font-space)]">
                <button
                  onClick={() => setRightTab("comms")}
                  className={`px-4 py-1.5 rounded-lg text-[12px] font-bold transition-all ${rightTab === "comms" ? "bg-[var(--color-neon-cyan)] text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "text-zinc-400 hover:text-white"}`}
                >
                  COMMS LOG
                </button>
                <button
                  onClick={() => setRightTab("draft")}
                  className={`px-4 py-1.5 rounded-lg text-[12px] font-bold transition-all flex items-center gap-2 ${rightTab === "draft" ? "bg-[var(--color-neon-cyan)] text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]" : "text-zinc-400 hover:text-white"}`}
                >
                  GENERATED DRAFT
                </button>
              </div>

              <div className="lg:hidden flex flex-wrap items-center gap-2 mb-3 bg-black border-4 border-black rounded-xl p-2 font-[var(--font-space)]">
                <span className={`text-[11px] font-bold uppercase ${gmailStatus?.connected ? "text-[var(--color-neon-green)]" : "text-zinc-400"}`}>
                  {gmailStatus?.connected ? "GMAIL CONNECTED" : "GMAIL DISCONNECTED"}
                </span>
                {gmailStatus?.connected && gmailStatus.read_sync_enabled ? (
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-[var(--color-neon-cyan)] text-black rounded-full border-2 border-black text-[11px] font-bold">
                    <SyncIcon size={12} strokeWidth={3} className={gmailSyncing ? "animate-spin" : ""} />
                    {syncLabel}
                  </div>
                ) : (
                  <button onClick={handleConnectGmail} disabled={!gmailStatus?.configured} className="px-3 py-1 bg-white text-black rounded-full border-2 border-black text-[11px] font-bold disabled:opacity-50">
                    {gmailStatus?.connected ? "RECONNECT FOR SYNC" : "CONNECT GMAIL"}
                  </button>
                )}
              </div>

              <AnimatePresence>
                {gmailNotice && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.98 }}
                    className="absolute top-20 right-5 z-40 max-w-[460px] bg-black border-4 border-[var(--color-neon-cyan)] rounded-xl px-4 py-3 text-[12px] text-[var(--color-neon-cyan)] font-bold font-[var(--font-space)] uppercase shadow-[4px_4px_0px_0px_var(--color-neon-cyan)]"
                  >
                    {gmailNotice}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Tab content */}
              <div className="flex-1 min-h-0 border-4 border-black bg-[var(--color-panel-bg)] rounded-2xl shadow-[4px_4px_0px_0px_var(--color-neon-cyan)] flex flex-col overflow-hidden">

                {/* ── COMMS LOG TAB ── */}
                {rightTab === "comms" && (
                  <div className="flex-1 flex flex-col overflow-hidden">
                    <div className="p-3 border-b-4 border-black bg-[var(--color-neon-cyan)] flex justify-between items-center font-[var(--font-space)]">
                      <h2 className="text-[13px] font-[var(--font-bungee)] text-black">COMMS LOG — {activePitch.venue_name.toUpperCase()}</h2>
                      <div className="flex items-center gap-2">
                        {gmailStatus?.connected && gmailStatus.read_sync_enabled && (
                          <div
                            className="flex items-center gap-2 px-2.5 py-1 bg-white text-black border-2 border-black text-[11px] font-bold rounded-full"
                          >
                            <SyncIcon size={12} strokeWidth={3} className={gmailSyncing ? "animate-spin" : ""} /> {syncLabel}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-6 space-y-5 font-sans">
                      {activeConv?.messages.map((msg, i) => (
                        <div key={i} className={`flex flex-col ${msg.direction === "outbound" ? "items-end" : "items-start"}`}>
                          <span className="text-[11px] font-bold text-white bg-[var(--color-panel-bg)] px-2 py-0.5 rounded border border-black uppercase mb-1.5 font-[var(--font-space)]">
                            {msg.direction === "outbound" ? entertainerName || "AGENT" : activePitch.venue_name}
                          </span>
                          <div className={`px-5 py-4 rounded-2xl border-4 border-black max-w-[88%] text-[16px] leading-[1.75] font-medium ${
                            msg.direction === "outbound"
                              ? "bg-[var(--color-neon-cyan)] text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-tr-none"
                              : "bg-white text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-tl-none"
                          }`}>
                            <CollapsibleText
                              text={msg.body}
                              textClassName="whitespace-pre-wrap"
                              buttonClassName={
                                msg.direction === "outbound"
                                  ? "bg-black text-[var(--color-neon-cyan)]"
                                  : "bg-[var(--color-neon-cyan)] text-black"
                              }
                            />
                          </div>
                        </div>
                      ))}
                      {(!activeConv || activeConv.messages.length === 0) && (
                        <p className="text-zinc-600 text-[13px] font-[var(--font-space)] uppercase">NO MESSAGES YET</p>
                      )}

                    </div>
                  </div>
                )}

                {/* ── GENERATED DRAFT TAB ── */}
                {rightTab === "draft" && (
                  <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Draft header */}
                    <div className="p-3 border-b-4 border-black bg-[var(--color-neon-cyan)] flex justify-between items-center font-[var(--font-space)] shrink-0">
                      <h2 className="text-[13px] font-[var(--font-bungee)] text-black">GENERATED DRAFT</h2>
                      <div className="flex items-center gap-3">
                        {activePitch.recipient_email && (
                          <span className="hidden lg:inline-flex text-[11px] font-bold text-black bg-white px-2 py-1 rounded-full border-2 border-black max-w-[260px] truncate">
                            TO: {activePitch.recipient_email}
                          </span>
                        )}
                        {isDrafting ? (
                          <span className="text-[11px] font-bold text-black flex items-center gap-2 bg-white px-2 py-1 rounded-full border-2 border-black">
                            <div className="w-2 h-2 rounded-full bg-black animate-pulse" /> DRAFTING
                          </span>
                        ) : (
                          <span className="text-[11px] font-bold text-white flex items-center gap-2 bg-black px-2 py-1 rounded-full border-2 border-black">
                            <div className="w-2 h-2 rounded-full bg-[var(--color-neon-cyan)]" /> READY
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Draft area */}
                    <div className="flex-1 p-6 overflow-y-auto">
                      {editingDraft ? (
                        <div className="relative min-h-[520px] h-full">
                          <textarea
                            value={draftText}
                            onChange={(e) => {
                              setDraftText(e.target.value);
                              setDraftEdited(true);
                            }}
                            className="w-full min-h-[520px] h-full bg-black border-4 border-[var(--color-neon-cyan)] rounded-xl p-6 text-[17px] text-white resize-none focus:outline-none font-sans leading-[1.75] shadow-[4px_4px_0px_0px_var(--color-neon-cyan)]"
                          />
                          <button
                            onClick={() => setEditingDraft(false)}
                            className="absolute top-3 right-3 px-3 py-1 bg-[var(--color-neon-cyan)] text-black text-[11px] font-bold rounded-lg border-2 border-black font-[var(--font-space)]"
                          >
                            DONE
                          </button>
                        </div>
                      ) : (
                        <div
                          className="min-h-[520px] h-full text-[17px] text-zinc-100 bg-black p-6 rounded-xl border-2 border-[var(--color-neon-cyan)] leading-[1.75] whitespace-pre-wrap cursor-pointer hover:border-white transition-colors group relative"
                          onClick={() => { setEditingDraft(true); setDraftText(currentDraft); }}
                        >
                          {currentDraft ? (
                            <>
                              <Typewriter key={currentDraft} text={currentDraft} onComplete={() => setIsDrafting(false)} />
                              <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="flex items-center gap-1 px-2 py-1 bg-zinc-800 border border-zinc-600 rounded-lg text-zinc-400 text-[11px] font-[var(--font-space)]">
                                  <Edit3 size={10} /> CLICK TO EDIT
                                </div>
                              </div>
                            </>
                          ) : (
                            <span className="text-zinc-600 font-[var(--font-space)] uppercase text-[14px]">SELECT A CONTACT TO VIEW DRAFT</span>
                          )}
                        </div>
                      )}

                      <AnimatePresence>
                        {isFinalized && (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="mt-4 bg-[var(--color-neon-cyan)] border-4 border-black text-black p-4 rounded-2xl flex items-center justify-between shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                          >
                            <div className="flex items-center gap-3">
                              <CheckCircle2 size={28} className="text-black bg-white rounded-full" />
                              <div>
                                <p className="text-[16px] font-[var(--font-bungee)]">PITCH APPROVED</p>
                                <p className="text-[12px] font-bold font-[var(--font-space)] uppercase">Agent 2 dispatching sequence.</p>
                              </div>
                            </div>
                            <button onClick={() => setIsFinalized(false)} className="text-[12px] font-bold bg-black text-white px-3 py-1.5 rounded-lg border-2 border-black font-[var(--font-space)]">UNDO</button>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>

                    {/* Controls footer */}
                    {!isFinalized && (
                      <div className="p-3 border-t-4 border-black bg-black shrink-0">
                        {/* Strategy adjustment */}
                        <div className="flex flex-wrap gap-2.5 font-[var(--font-space)]">
                          <input
                            type="text"
                            value={strategyInput}
                            onChange={(e) => setStrategyInput(e.target.value)}
                            placeholder="Pitch adjustment instructions..."
                            className="flex-1 min-w-[260px] bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-cyan)] rounded-xl px-4 py-2 text-[14px] font-bold text-white placeholder-[var(--color-neon-cyan)]/40 focus:outline-none focus:border-white transition-colors font-sans"
                            onKeyDown={(e) => e.key === "Enter" && handleAdjustPitch()}
                          />
                          <button
                            onClick={handleAdjustPitch}
                            className="flex items-center gap-2 px-4 py-2 bg-[var(--color-neon-cyan)] border-4 border-black text-black text-[12px] font-bold rounded-full hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] transition-all uppercase"
                          >
                            <RefreshCw size={14} strokeWidth={3} /> REGENERATE
                          </button>
                          <button
                            disabled={isDrafting}
                            onClick={handleDiscard}
                            className="px-4 py-2 bg-[var(--color-panel-bg)] border-2 border-red-800 text-red-400 text-[12px] font-bold rounded-xl hover:bg-red-950 transition-all disabled:opacity-40 uppercase"
                          >
                            DISCARD
                          </button>
                          {autoMode && !draftEdited ? (
                            <div className="px-4 py-2 bg-zinc-900 border-2 border-[var(--color-neon-cyan)] text-[var(--color-neon-cyan)] text-[12px] font-bold rounded-xl uppercase">
                              AUTO SENDS WITHOUT APPROVAL
                            </div>
                          ) : (
                            <button
                              disabled={isDrafting}
                              onClick={handleApprove}
                              className="px-5 py-2 bg-[var(--color-neon-cyan)] text-black border-4 border-black text-[12px] font-[var(--font-bungee)] rounded-xl hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] transition-all flex items-center gap-2 disabled:opacity-40 disabled:pointer-events-none"
                            >
                              <Send size={16} strokeWidth={3} />
                              {autoMode ? "SEND EDIT" : "APPROVE & SEND"}
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 border-4 border-black bg-[var(--color-panel-bg)] rounded-2xl shadow-[6px_6px_0px_0px_var(--color-neon-cyan)] flex items-center justify-center">
              <p className="text-zinc-600 text-[14px] font-[var(--font-space)] uppercase">SELECT A CONTACT OR SEND VENUES FROM MARKET SCAN</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
