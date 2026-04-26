import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { RefreshCw, FileText, Send, Check, Calendar, DollarSign } from "lucide-react";
import { client } from "../api/client";
import { CollapsibleText } from "../components/CollapsibleText";

type LogItem = {
  id: string;
  label: string;
  direction: string;
  body: string;
  status?: string;
  created_at?: string;
  bookingId?: string;
};

export function Pipeline() {
  const [bookings, setBookings] = useState<any[]>([]);
  const [messages, setMessages] = useState<Record<string, any[]>>({});
  const [conversationMessages, setConversationMessages] = useState<Record<string, any[]>>({});
  const [rebookTargets, setRebookTargets] = useState<any[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [selectedRebooks, setSelectedRebooks] = useState<Set<string>>(new Set());
  const [initiatingRebook, setInitiatingRebook] = useState(false);
  const [rebookedIds, setRebookedIds] = useState<Set<string>>(new Set());
  const [pendingFollowups, setPendingFollowups] = useState<any[]>([]);
  const [sendingFollowup, setSendingFollowup] = useState<string | null>(null);
  const [entertainerId, setEntertainerId] = useState("");
  const [resolvingDealId, setResolvingDealId] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const entertainers = await client.entertainers.active();
      if (!entertainers.length) return;
      const ent = entertainers[0];
      setEntertainerId(ent.id);
      const [active, followups] = await Promise.all([
        client.bookings.active(),
        client.outreach.pendingFollowups(),
      ]);
      setBookings(active);
      setPendingFollowups(followups);
      setSelectedDealId(active[0]?.id || null);

      const msgMap: Record<string, any[]> = {};
      const convMap: Record<string, any[]> = {};
      await Promise.all(active.map(async (booking: any) => {
        try { msgMap[booking.id] = await client.bookings.messages(booking.id); } catch { msgMap[booking.id] = []; }
        try {
          const conv = await client.conversations.get(booking.target_id);
          convMap[booking.id] = conv.messages || [];
        } catch {
          convMap[booking.id] = [];
        }
      }));
      setMessages(msgMap);
      setConversationMessages(convMap);

      try {
        const completed = await client.bookings.completedUnrebooked();
        setRebookTargets(completed || []);
      } catch {
        setRebookTargets([]);
      }
    })();
  }, []);

  const selectedDeal = bookings.find((booking) => booking.id === selectedDealId) || bookings[0];

  const selectedLog: LogItem[] = selectedDeal ? [
    ...(conversationMessages[selectedDeal.id] || []).map((msg: any) => ({
      id: `conv-${msg.id}`,
      label: msg.direction === "outbound" ? "OUTREACH" : selectedDeal.venue_name,
      direction: msg.direction,
      body: msg.body,
      status: msg.message_type,
      created_at: msg.created_at,
    })),
    ...(messages[selectedDeal.id] || []).map((msg: any) => ({
      id: `booking-${msg.id}`,
      label: "AGENT 4",
      direction: "outbound",
      body: msg.body,
      status: msg.status,
      created_at: msg.created_at,
      bookingId: selectedDeal.id,
    })),
  ].sort((a, b) => String(a.created_at || "").localeCompare(String(b.created_at || ""))) : [];

  const allRebookTargets = rebookTargets;

  const toggleRebook = (id: string) => {
    setSelectedRebooks((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleInitiateSelected = async () => {
    if (!selectedRebooks.size || initiatingRebook || !entertainerId) return;
    setInitiatingRebook(true);
    const targets = allRebookTargets.filter((target) => selectedRebooks.has(target.id));
    const initiated = new Set<string>();

    await Promise.all(targets.map(async (target) => {
      try {
        await client.outreach.createRebookPitch({
          entertainer_id: entertainerId,
          booking_id: target.id,
          status: "draft",
        });
        initiated.add(target.id);
      } catch {}
    }));

    setRebookedIds((prev) => new Set([...prev, ...initiated]));
    setRebookTargets((prev) => prev.filter((target) => !initiated.has(target.id)));
    setSelectedRebooks(new Set());
    setInitiatingRebook(false);
  };

  const handleMarkFollowupSent = async (followupId: string) => {
    setSendingFollowup(followupId);
    try {
      await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/outreach/followup/${followupId}`, { method: "PATCH" });
      setPendingFollowups((prev) => prev.filter((f) => (f.id || f.pitch_id) !== followupId));
    } catch {}
    setSendingFollowup(null);
  };

  const handleMarkBookingMsgSent = async (msgId: string, bookingId: string) => {
    await client.bookings.markBookingMessageSent(msgId);
    const updated = await client.bookings.messages(bookingId);
    setMessages((prev) => ({ ...prev, [bookingId]: updated }));
  };

  const handleResolvePerformance = async (booking: any) => {
    if (!booking?.id || resolvingDealId === booking.id) return;
    setResolvingDealId(booking.id);
    try {
      const resolved = await client.bookings.resolvePerformance(booking.id);
      setBookings((prev) => {
        const next = prev.filter((item) => item.id !== booking.id);
        if (selectedDealId === booking.id) setSelectedDealId(next[0]?.id || null);
        return next;
      });
      setMessages((prev) => {
        const next = { ...prev };
        delete next[booking.id];
        return next;
      });
      setConversationMessages((prev) => {
        const next = { ...prev };
        delete next[booking.id];
        return next;
      });
      setRebookTargets((prev) => (
        prev.some((item) => item.id === resolved.id) ? prev : [resolved, ...prev]
      ));
    } catch {
      window.alert("Could not move this deal to the rebook engine yet.");
    } finally {
      setResolvingDealId(null);
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden pr-1 pb-1">
      <div className="bg-[var(--color-panel-bg)] border-4 border-black p-3 rounded-2xl shadow-[4px_4px_0px_0px_var(--color-neon-yellow)] flex justify-between items-center shrink-0 mb-3">
        <h1 className="text-base font-[var(--font-bungee)] text-white bg-black px-4 py-1.5 rounded-full border-4 border-[var(--color-neon-yellow)] uppercase tracking-wider">AGENT 4 :: PIPELINE</h1>
        <div className="flex gap-2 font-[var(--font-space)]">
          <span className="bg-black border-2 border-[var(--color-neon-yellow)] px-3 py-1 rounded-full text-[var(--color-neon-yellow)] font-bold text-[11px]">
            {bookings.length} SECURED
          </span>
          <span className="bg-black border-2 border-[var(--color-neon-yellow)] px-3 py-1 rounded-full text-[var(--color-neon-yellow)] font-bold text-[11px]">
            {pendingFollowups.length} FOLLOWUPS DUE
          </span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden gap-3 pr-1 pb-1 min-h-0 font-sans">
        <div className="w-64 shrink-0 bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-3 overflow-y-auto shadow-[4px_4px_0px_0px_var(--color-neon-yellow)]">
          <h2 className="text-[12px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] mb-3 bg-black px-3 py-1 rounded-full border-2 border-[var(--color-neon-yellow)] inline-block">
            SECURED DEALS
          </h2>
          <div className="space-y-2">
            {bookings.map((booking) => (
              <div key={booking.id} className="relative overflow-hidden rounded-xl">
                <div className="absolute inset-0 bg-[var(--color-neon-green)] border-4 border-black rounded-xl flex items-center justify-end pr-4 text-black font-[var(--font-bungee)] text-[11px]">
                  READY TO REBOOK
                </div>
                <motion.div
                  drag="x"
                  dragConstraints={{ left: -105, right: 0 }}
                  dragElastic={0.08}
                  dragSnapToOrigin
                  onDragEnd={(_, info) => {
                    if (info.offset.x < -82 || info.velocity.x < -520) handleResolvePerformance(booking);
                  }}
                  role="button"
                  tabIndex={0}
                  onClick={() => setSelectedDealId(booking.id)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" || event.key === " ") setSelectedDealId(booking.id);
                  }}
                  className={`relative w-full text-left px-3 py-2.5 rounded-xl border-4 transition-all cursor-pointer ${
                    selectedDeal?.id === booking.id
                      ? "bg-[var(--color-neon-yellow)] text-black border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] -translate-y-0.5"
                      : "bg-black text-white border-black hover:border-[var(--color-neon-yellow)]"
                  } ${resolvingDealId === booking.id ? "opacity-60 pointer-events-none" : ""}`}
                >
                  <div className="flex justify-between gap-3">
                    <p className="text-[13px] font-bold leading-tight">{booking.venue_name}</p>
                    <FileText size={14} className="shrink-0 mt-0.5" strokeWidth={3} />
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-2 font-[var(--font-space)]">
                    <span className="flex items-center gap-1 text-[10px] font-bold uppercase">
                      <DollarSign size={11} strokeWidth={3} /> {booking.agreed_rate ? `${booking.agreed_rate}` : "TBD"}
                    </span>
                    <span className="flex items-center gap-1 text-[10px] font-bold uppercase justify-end">
                      <Calendar size={11} strokeWidth={3} /> {booking.show_date || "DATE TBD"}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full uppercase font-[var(--font-space)] ${selectedDeal?.id === booking.id ? "bg-black text-[var(--color-neon-yellow)]" : "bg-zinc-800 text-zinc-400"}`}>
                      {(booking.conversation_stage || "confirmed").replace(/_/g, " ")}
                    </span>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        handleResolvePerformance(booking);
                      }}
                      disabled={resolvingDealId === booking.id}
                      className={`flex items-center gap-1 px-2 py-1 rounded-lg border-2 border-black text-[10px] font-bold font-[var(--font-space)] uppercase ${
                        selectedDeal?.id === booking.id
                          ? "bg-white text-black"
                          : "bg-[var(--color-neon-yellow)] text-black"
                      } disabled:opacity-50`}
                    >
                      <Check size={10} strokeWidth={3} />
                      {resolvingDealId === booking.id ? "MOVING" : "RESOLVE"}
                    </button>
                  </div>
                </motion.div>
              </div>
            ))}
            {bookings.length === 0 && (
              <p className="text-zinc-600 text-[12px] font-[var(--font-space)] uppercase p-2">NO SECURED DEALS YET.</p>
            )}
          </div>

          {pendingFollowups.length > 0 && (
            <div className="mt-4 pt-4 border-t-4 border-black">
              <h3 className="text-[12px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] mb-3">FOLLOWUPS DUE</h3>
              <div className="space-y-2">
                {pendingFollowups.map((followup: any) => {
                  const followupId = followup.id || followup.pitch_id;
                  return (
                    <div key={followupId} className="bg-black border-2 border-[var(--color-neon-yellow)]/50 p-2.5 rounded-xl">
                      <p className="text-white font-bold text-[12px]">{followup.venue_name}</p>
                      <button
                        onClick={() => handleMarkFollowupSent(followupId)}
                        disabled={!followup.id || sendingFollowup === followupId}
                        className="mt-2 px-3 py-1.5 bg-[var(--color-neon-yellow)] text-black text-[10px] font-bold rounded-lg border-2 border-black disabled:opacity-40 font-[var(--font-space)]"
                      >
                        {sendingFollowup === followupId ? "SENDING..." : followup.id ? "MARK SENT" : "WAITING FOR DRAFT"}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0 flex flex-col gap-3">
          <section className="flex-1 min-h-0 bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl shadow-[4px_4px_0px_0px_var(--color-neon-yellow)] flex flex-col overflow-hidden">
            <div className="p-3 border-b-4 border-black bg-[var(--color-neon-yellow)] flex justify-between items-center font-[var(--font-space)] shrink-0">
              <h2 className="text-[13px] font-[var(--font-bungee)] text-black">
                INTERACTION LOG{selectedDeal ? ` - ${selectedDeal.venue_name.toUpperCase()}` : ""}
              </h2>
              <span className="text-[11px] font-bold text-black bg-white border-2 border-black px-2 py-1 rounded-full">
                {selectedLog.length} EVENTS
              </span>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {selectedLog.map((item, idx) => (
                <div key={item.id} className="flex gap-4">
                  <div className="flex flex-col items-center mt-1">
                    <div className={`w-4 h-4 rounded-sm border-2 border-black ${item.direction === "outbound" ? "bg-[var(--color-neon-yellow)]" : "bg-white"}`} />
                    {idx !== selectedLog.length - 1 && <div className="w-[3px] flex-1 bg-black my-1.5" />}
                  </div>
                  <div className="bg-black p-5 rounded-xl border-2 border-[var(--color-neon-yellow)]/50 flex-1 shadow-[3px_3px_0px_0px_rgba(209,209,42,0.22)]">
                    <div className="flex items-center justify-between gap-3 mb-3">
                      <p className="text-[12px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)]">{item.label.toUpperCase()}</p>
                      {item.status && (
                        <span className="text-[11px] font-bold text-zinc-400 font-[var(--font-space)] uppercase">{String(item.status).replace(/_/g, " ")}</span>
                      )}
                    </div>
                    <CollapsibleText
                      text={item.body}
                      textClassName="text-[16px] font-medium text-zinc-100 leading-[1.75] whitespace-pre-wrap"
                      buttonClassName="bg-[var(--color-neon-yellow)] text-black"
                    />
                    {item.id.startsWith("booking-") && item.status === "draft" && item.bookingId && (
                      <button
                        onClick={() => handleMarkBookingMsgSent(item.id.replace("booking-", ""), item.bookingId!)}
                        className="mt-3 px-3 py-1.5 bg-[var(--color-neon-yellow)] text-black text-[11px] font-bold rounded-lg border-2 border-black flex items-center gap-1.5 hover:-translate-y-0.5 transition-all font-[var(--font-space)]"
                      >
                        <Send size={11} strokeWidth={3} /> MARK SENT
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {selectedDeal && selectedLog.length === 0 && (
                <p className="text-zinc-600 text-[15px] font-[var(--font-space)] uppercase">NO LOGISTICS MESSAGES YET. AGENT 4 WILL DRAFT THE NEXT CHECK-IN.</p>
              )}
              {!selectedDeal && (
                <p className="text-zinc-600 text-[15px] font-[var(--font-space)] uppercase">SELECT A SECURED DEAL TO VIEW ITS LOG.</p>
              )}
            </div>
          </section>

          <section className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-3 shadow-[3px_3px_0px_0px_var(--color-neon-yellow)] shrink-0 max-h-[190px] overflow-y-auto">
            <div className="flex flex-wrap justify-between items-center gap-3 border-b-4 border-black pb-2 mb-3">
              <h2 className="text-[13px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] flex items-center gap-2">
                <RefreshCw size={16} strokeWidth={3} /> REBOOK ENGINE
              </h2>
              {selectedRebooks.size > 0 && (
                <AnimatePresence>
                  <motion.button
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={handleInitiateSelected}
                    disabled={initiatingRebook}
                    className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-neon-yellow)] text-black border-4 border-black text-[11px] font-[var(--font-bungee)] rounded-xl hover:-translate-y-0.5 hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] transition-all disabled:opacity-50"
                  >
                    {initiatingRebook ? "INITIATING..." : <><Send size={13} strokeWidth={3} /> SEND {selectedRebooks.size} TO OUTREACH</>}
                  </motion.button>
                </AnimatePresence>
              )}
            </div>
            {allRebookTargets.length === 0 ? (
              <div className="bg-black border-2 border-[var(--color-neon-yellow)]/40 rounded-xl p-4">
                <p className="text-[12px] text-zinc-400 font-[var(--font-space)] uppercase leading-relaxed">
                  NO COMPLETED DEALS READY FOR REBOOK YET. COMPLETED BOOKINGS WILL APPEAR HERE.
                </p>
              </div>
            ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3">
              {allRebookTargets.map((target: any) => (
                <RebookCard
                  key={target.id}
                  id={target.id}
                  venueName={target.venue_name}
                  note={target.rebook_note || "Completed show is ready for a rebook outreach draft."}
                  selected={selectedRebooks.has(target.id)}
                  rebooked={rebookedIds.has(target.id)}
                  onToggle={toggleRebook}
                />
              ))}
            </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

function RebookCard({ id, venueName, note, selected, rebooked, onToggle }: {
  id: string; venueName: string; note: string; selected: boolean; rebooked: boolean; onToggle: (id: string) => void;
}) {
  return (
    <motion.div
      layout
      className={`bg-black border-4 rounded-xl p-3 transition-all ${
        rebooked ? "border-[var(--color-neon-green)] opacity-80" :
        selected ? "border-[var(--color-neon-yellow)] shadow-[3px_3px_0px_0px_var(--color-neon-yellow)]" :
        "border-black shadow-[2px_2px_0px_0px_rgba(255,209,42,0.25)]"
      }`}
    >
      <div className="flex justify-between items-start gap-3 mb-2">
        <h3 className="text-[13px] font-[var(--font-bungee)] text-white leading-snug">{venueName}</h3>
        {rebooked ? (
          <span className="flex items-center gap-1 text-[10px] font-bold text-[var(--color-neon-green)] font-[var(--font-space)] bg-[var(--color-neon-green)]/20 border border-[var(--color-neon-green)] px-2 py-1 rounded-full">
            <Check size={10} strokeWidth={3} /> QUEUED
          </span>
        ) : (
          <span className="text-[10px] font-bold bg-[var(--color-neon-yellow)] text-black px-2 py-1 rounded-full border-2 border-black font-[var(--font-space)] uppercase">REBOOK</span>
        )}
      </div>
      <p className="text-[12px] font-medium text-zinc-300 mb-3 border-l-4 border-[var(--color-neon-yellow)] pl-3 leading-relaxed">{note}</p>
      {!rebooked && (
        <button
          onClick={() => onToggle(id)}
          className={`w-full py-1.5 border-4 border-black text-[11px] font-[var(--font-bungee)] rounded-xl transition-all ${
            selected
              ? "bg-[var(--color-neon-yellow)] text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              : "bg-[var(--color-panel-bg)] text-[var(--color-neon-yellow)] hover:bg-[var(--color-neon-yellow)] hover:text-black"
          }`}
        >
          {selected ? "SELECTED" : "SELECT"}
        </button>
      )}
    </motion.div>
  );
}
