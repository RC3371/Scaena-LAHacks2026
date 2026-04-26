import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  AlertTriangle,
  Calendar,
  Check,
  ClipboardCheck,
  Clock,
  DollarSign,
  FileText,
  NotebookPen,
  RefreshCw,
  Save,
  Send,
} from "lucide-react";
import { client } from "../api/client";
import { CollapsibleText } from "../components/CollapsibleText";
import { loadPageState, savePageState } from "../utils/pagePersistence";

type LogItem = {
  id: string;
  label: string;
  direction: string;
  body: string;
  status?: string;
  created_at?: string;
  bookingId?: string;
};

type BookingDraft = {
  show_date: string;
  agreed_rate: string;
  post_show_notes: string;
  crowd_size: string;
  audience_reaction: string;
  venue_satisfaction: string;
  payout_received: boolean;
  rebook_recommended: boolean;
};

const STAGES = [
  { id: "secured", label: "Secured" },
  { id: "logistics_pending", label: "Logistics" },
  { id: "show_scheduled", label: "Scheduled" },
  { id: "post_show_followup", label: "Post-show" },
  { id: "rebook_ready", label: "Rebook Ready" },
];

const CHECKLIST_ITEMS = [
  ["date_confirmed", "Date"],
  ["rate_confirmed", "Rate"],
  ["contact_confirmed", "Contact"],
  ["set_length_confirmed", "Set length"],
  ["load_in_confirmed", "Load-in"],
  ["payment_confirmed", "Payment"],
  ["promo_assets_sent", "Promo assets"],
  ["contract_invoice_sent", "Contract/invoice"],
] as const;

const blankDraft: BookingDraft = {
  show_date: "",
  agreed_rate: "",
  post_show_notes: "",
  crowd_size: "",
  audience_reaction: "",
  venue_satisfaction: "",
  payout_received: false,
  rebook_recommended: true,
};

function draftFromBooking(booking: any): BookingDraft {
  if (!booking) return blankDraft;
  return {
    show_date: booking.show_date || "",
    agreed_rate: booking.agreed_rate ? String(booking.agreed_rate) : "",
    post_show_notes: booking.post_show_notes || "",
    crowd_size: booking.crowd_size ? String(booking.crowd_size) : "",
    audience_reaction: booking.audience_reaction || "",
    venue_satisfaction: booking.venue_satisfaction || "",
    payout_received: Boolean(booking.payout_received),
    rebook_recommended: booking.rebook_recommended !== false,
  };
}

function stageLabel(stage?: string) {
  return STAGES.find((item) => item.id === stage)?.label || String(stage || "secured").replace(/_/g, " ");
}

function healthClasses(health?: string) {
  const value = String(health || "").toLowerCase();
  if (value.includes("ready") || value.includes("sent")) return "text-[var(--color-neon-green)] border-[var(--color-neon-green)]";
  if (value.includes("risk") || value.includes("needs")) return "text-[var(--color-neon-yellow)] border-[var(--color-neon-yellow)]";
  return "text-white border-white";
}

export function Pipeline() {
  const [bookings, setBookings] = useState<any[]>([]);
  const [messages, setMessages] = useState<Record<string, any[]>>({});
  const [conversationMessages, setConversationMessages] = useState<Record<string, any[]>>({});
  const [rebookTargets, setRebookTargets] = useState<any[]>([]);
  const [selectedDealId, setSelectedDealId] = useState<string | null>(null);
  const [selectedRebooks, setSelectedRebooks] = useState<Set<string>>(new Set());
  const [initiatingRebook, setInitiatingRebook] = useState(false);
  const [rebookedIds, setRebookedIds] = useState<Set<string>>(new Set());
  const [autoMode, setAutoMode] = useState(true);
  const [rebookNotice, setRebookNotice] = useState("");
  const [pendingFollowups, setPendingFollowups] = useState<any[]>([]);
  const [sendingFollowup, setSendingFollowup] = useState<string | null>(null);
  const [entertainerId, setEntertainerId] = useState("");
  const [savingDealId, setSavingDealId] = useState<string | null>(null);
  const [draft, setDraft] = useState<BookingDraft>(blankDraft);

  const selectedDeal = bookings.find((booking) => booking.id === selectedDealId) || bookings[0] || null;

  const loadPipeline = async () => {
    const entertainers = await client.entertainers.active();
    if (!entertainers.length) return;
    const ent = entertainers[0];
    const saved = loadPageState(`scaena.ui.pipeline.${ent.id}`, {
      selectedDealId: null as string | null,
      selectedRebookIds: [] as string[],
    });
    setEntertainerId(ent.id);
    setAutoMode(ent.outreach_mode === "auto_pitch");
    const [active, followups, completed] = await Promise.all([
      client.bookings.active(),
      client.outreach.pendingFollowups(),
      client.bookings.completedUnrebooked().catch(() => []),
    ]);
    setBookings(active || []);
    setPendingFollowups(followups || []);
    setRebookTargets(completed || []);
    setSelectedRebooks(new Set(saved.selectedRebookIds || []));
    setSelectedDealId((current) => {
      if (current) return current;
      if (saved.selectedDealId && active?.some((booking: any) => booking.id === saved.selectedDealId)) {
        return saved.selectedDealId;
      }
      return active?.[0]?.id || null;
    });

    const msgMap: Record<string, any[]> = {};
    const convMap: Record<string, any[]> = {};
    await Promise.all((active || []).map(async (booking: any) => {
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
  };

  useEffect(() => {
    loadPipeline();
  }, []);

  useEffect(() => {
    if (!entertainerId) return;
    savePageState(`scaena.ui.pipeline.${entertainerId}`, {
      selectedDealId,
      selectedRebookIds: Array.from(selectedRebooks),
    });
  }, [selectedDealId, selectedRebooks, entertainerId]);

  useEffect(() => {
    setDraft(draftFromBooking(selectedDeal));
  }, [selectedDeal?.id]);

  const selectedLog: LogItem[] = useMemo(() => selectedDeal ? [
    ...(conversationMessages[selectedDeal.id] || []).map((msg: any) => ({
      id: `conv-${msg.id}`,
      label: msg.direction === "outbound" ? "Outreach" : selectedDeal.venue_name,
      direction: msg.direction,
      body: msg.body,
      status: msg.message_type,
      created_at: msg.created_at,
    })),
    ...(messages[selectedDeal.id] || []).map((msg: any) => ({
      id: `booking-${msg.id}`,
      label: "Agent 4",
      direction: "outbound",
      body: msg.body,
      status: msg.status,
      created_at: msg.created_at,
      bookingId: selectedDeal.id,
    })),
  ].sort((a, b) => String(a.created_at || "").localeCompare(String(b.created_at || ""))) : [], [conversationMessages, messages, selectedDeal]);

  const updateBookingInState = (updated: any) => {
    setBookings((prev) => prev.map((item) => item.id === updated.id ? updated : item));
    setRebookTargets((prev) => prev.map((item) => item.id === updated.id ? updated : item));
  };

  const updatePipeline = async (payload: Record<string, unknown>) => {
    if (!selectedDeal) return null;
    setSavingDealId(selectedDeal.id);
    try {
      const updated = await client.bookings.updatePipeline(selectedDeal.id, payload);
      updateBookingInState(updated);
      return updated;
    } finally {
      setSavingDealId(null);
    }
  };

  const handleSaveDetails = async () => {
    await updatePipeline({
      show_date: draft.show_date || null,
      agreed_rate: draft.agreed_rate ? Number(draft.agreed_rate) : null,
      post_show_notes: draft.post_show_notes || null,
      crowd_size: draft.crowd_size ? Number(draft.crowd_size) : null,
      audience_reaction: draft.audience_reaction || null,
      venue_satisfaction: draft.venue_satisfaction || null,
      payout_received: draft.payout_received,
      rebook_recommended: draft.rebook_recommended,
    });
  };

  const handleChecklistToggle = async (key: string, value: boolean) => {
    await updatePipeline({ logistics_checklist: { [key]: value } });
  };

  const handleResolvePerformance = async () => {
    if (!selectedDeal) return;
    setSavingDealId(selectedDeal.id);
    try {
      const resolved = await client.bookings.resolvePerformanceWithNotes(selectedDeal.id, {
        post_show_notes: draft.post_show_notes || null,
        crowd_size: draft.crowd_size ? Number(draft.crowd_size) : null,
        audience_reaction: draft.audience_reaction || null,
        payout_received: draft.payout_received,
        venue_satisfaction: draft.venue_satisfaction || null,
        rebook_recommended: draft.rebook_recommended,
      });
      setBookings((prev) => {
        const next = prev.filter((item) => item.id !== selectedDeal.id);
        setSelectedDealId(next[0]?.id || null);
        return next;
      });
      setMessages((prev) => {
        const next = { ...prev };
        delete next[selectedDeal.id];
        return next;
      });
      setConversationMessages((prev) => {
        const next = { ...prev };
        delete next[selectedDeal.id];
        return next;
      });
      if (resolved.conversation_stage === "rebook_ready") {
        setRebookTargets((prev) => prev.some((item) => item.id === resolved.id) ? prev : [resolved, ...prev]);
      }
    } finally {
      setSavingDealId(null);
    }
  };

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
    setRebookNotice("");
    const targets = rebookTargets.filter((target) => selectedRebooks.has(target.id));
    const initiated = new Set<string>();
    const emailed = new Set<string>();
    const createFailures: string[] = [];
    const sendFailures: string[] = [];

    await Promise.all(targets.map(async (target) => {
      try {
        const result = await client.outreach.createRebookPitch({
          entertainer_id: entertainerId,
          booking_id: target.id,
          status: "draft",
        });
        initiated.add(target.id);

        if (autoMode && result?.pitch_id) {
          try {
            await client.gmail.sendPitch(result.pitch_id);
            emailed.add(target.id);
          } catch {
            sendFailures.push(target.venue_name || "rebook target");
          }
        }
      } catch {
        createFailures.push(target.venue_name || "rebook target");
      }
    }));

    setRebookedIds((prev) => new Set([...prev, ...initiated]));
    setRebookTargets((prev) => prev.filter((target) => !initiated.has(target.id)));
    setSelectedRebooks(new Set());
    if (autoMode) {
      const failedText = sendFailures.length ? ` ${sendFailures.length} could not email and stayed as drafts.` : "";
      const createText = createFailures.length ? ` ${createFailures.length} could not be created.` : "";
      setRebookNotice(`Auto emailed ${emailed.size}/${initiated.size} rebook requests.${failedText}${createText}`);
    } else if (initiated.size) {
      const createText = createFailures.length ? ` ${createFailures.length} could not be created.` : "";
      setRebookNotice(`Created ${initiated.size} rebook drafts in Outreach.${createText}`);
    } else if (createFailures.length) {
      setRebookNotice("Rebook request could not be created.");
    }
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
    await loadPipeline();
  };

  const checklist = selectedDeal?.logistics_checklist || {};
  const checklistDone = CHECKLIST_ITEMS.filter(([key]) => checklist[key]).length;

  return (
    <div className="flex flex-col h-full overflow-hidden pr-1 pb-1">
      <div className="bg-[var(--color-panel-bg)] border-4 border-black p-3 rounded-2xl shadow-[4px_4px_0px_0px_var(--color-neon-yellow)] flex justify-between items-center shrink-0 mb-3">
        <h1 className="text-base font-[var(--font-bungee)] text-white bg-black px-4 py-1.5 rounded-full border-4 border-[var(--color-neon-yellow)] uppercase tracking-wider">AGENT 4 :: PIPELINE</h1>
        <div className="flex gap-2 font-[var(--font-space)]">
          <span className="bg-black border-2 border-[var(--color-neon-yellow)] px-3 py-1 rounded-full text-[var(--color-neon-yellow)] font-bold text-[11px]">
            {bookings.length} ACTIVE
          </span>
          <span className="bg-black border-2 border-[var(--color-neon-green)] px-3 py-1 rounded-full text-[var(--color-neon-green)] font-bold text-[11px]">
            {rebookTargets.length} REBOOK READY
          </span>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden gap-3 pr-1 pb-1 min-h-0 font-sans">
        <aside className="w-72 shrink-0 bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-3 overflow-y-auto shadow-[4px_4px_0px_0px_var(--color-neon-yellow)]">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[12px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] bg-black px-3 py-1 rounded-full border-2 border-[var(--color-neon-yellow)]">
              SECURED DEALS
            </h2>
          </div>

          <div className="space-y-2">
            {bookings.map((booking) => (
              <button
                key={booking.id}
                type="button"
                onClick={() => setSelectedDealId(booking.id)}
                className={`w-full text-left px-3 py-3 rounded-xl border-4 transition-all ${
                  selectedDeal?.id === booking.id
                    ? "bg-[var(--color-neon-yellow)] text-black border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]"
                    : "bg-black text-white border-black hover:border-[var(--color-neon-yellow)]"
                }`}
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
                    {stageLabel(booking.conversation_stage)}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border font-[var(--font-space)] ${selectedDeal?.id === booking.id ? "bg-white text-black border-black" : healthClasses(booking.pipeline_health)}`}>
                    {booking.pipeline_health || "on track"}
                  </span>
                </div>
              </button>
            ))}
            {bookings.length === 0 && (
              <p className="text-zinc-600 text-[12px] font-[var(--font-space)] uppercase p-2">NO ACTIVE DEALS YET.</p>
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
        </aside>

        <main className="flex-1 min-w-0 flex flex-col gap-3">
          <section className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl shadow-[4px_4px_0px_0px_var(--color-neon-yellow)] overflow-hidden shrink-0">
            <div className="p-3 border-b-4 border-black bg-[var(--color-neon-yellow)] flex justify-between items-center font-[var(--font-space)]">
              <h2 className="text-[13px] font-[var(--font-bungee)] text-black">
                DEAL COMMAND{selectedDeal ? ` - ${selectedDeal.venue_name.toUpperCase()}` : ""}
              </h2>
              {selectedDeal && (
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-[11px] font-bold text-black bg-white border-2 border-black px-2 py-1 rounded-full uppercase shrink-0">
                    {stageLabel(selectedDeal.conversation_stage)}
                  </span>
                  <span className="text-[11px] font-bold text-black bg-white border-2 border-black px-2 py-1 rounded-full uppercase truncate max-w-[520px]">
                    {selectedDeal.next_action || "monitor"}
                  </span>
                </div>
              )}
            </div>

            {selectedDeal ? (
              <div className="p-3 grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-3">
                <div className="space-y-3">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <Field label="Show date">
                      <input
                        type="date"
                        value={draft.show_date}
                        onChange={(event) => setDraft((prev) => ({ ...prev, show_date: event.target.value }))}
                        className="w-full bg-black border-2 border-zinc-700 rounded-lg px-2 py-2 text-white text-[13px] font-[var(--font-space)]"
                      />
                    </Field>
                    <Field label="Rate">
                      <input
                        type="number"
                        value={draft.agreed_rate}
                        onChange={(event) => setDraft((prev) => ({ ...prev, agreed_rate: event.target.value }))}
                        className="w-full bg-black border-2 border-zinc-700 rounded-lg px-2 py-2 text-white text-[13px] font-[var(--font-space)]"
                        placeholder="350"
                      />
                    </Field>
                    <Field label="Crowd">
                      <input
                        type="number"
                        value={draft.crowd_size}
                        onChange={(event) => setDraft((prev) => ({ ...prev, crowd_size: event.target.value }))}
                        className="w-full bg-black border-2 border-zinc-700 rounded-lg px-2 py-2 text-white text-[13px] font-[var(--font-space)]"
                        placeholder="1000"
                      />
                    </Field>
                    <Field label="Reaction">
                      <select
                        value={draft.audience_reaction}
                        onChange={(event) => setDraft((prev) => ({ ...prev, audience_reaction: event.target.value }))}
                        className="w-full bg-black border-2 border-zinc-700 rounded-lg px-2 py-2 text-white text-[13px] font-[var(--font-space)]"
                      >
                        <option value="">TBD</option>
                        <option value="strong">Strong</option>
                        <option value="solid">Solid</option>
                        <option value="mixed">Mixed</option>
                      </select>
                    </Field>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-[1fr_180px_180px] gap-2">
                    <textarea
                      value={draft.post_show_notes}
                      onChange={(event) => setDraft((prev) => ({ ...prev, post_show_notes: event.target.value }))}
                      className="min-h-[92px] bg-black border-2 border-zinc-700 rounded-xl px-3 py-2 text-white text-[14px] leading-relaxed resize-none"
                      placeholder="Post-show notes, crowd reaction, payout notes, and rebook context..."
                    />
                    <label className="bg-black border-2 border-zinc-700 rounded-xl p-3 flex items-center gap-2 text-[12px] font-bold text-white font-[var(--font-space)] uppercase">
                      <input
                        type="checkbox"
                        checked={draft.payout_received}
                        onChange={(event) => setDraft((prev) => ({ ...prev, payout_received: event.target.checked }))}
                        className="size-4 accent-[var(--color-neon-yellow)]"
                      />
                      Payout received
                    </label>
                    <label className="bg-black border-2 border-zinc-700 rounded-xl p-3 flex items-center gap-2 text-[12px] font-bold text-white font-[var(--font-space)] uppercase">
                      <input
                        type="checkbox"
                        checked={draft.rebook_recommended}
                        onChange={(event) => setDraft((prev) => ({ ...prev, rebook_recommended: event.target.checked }))}
                        className="size-4 accent-[var(--color-neon-yellow)]"
                      />
                      Rebook recommended
                    </label>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="bg-black border-4 border-black rounded-xl p-3">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-[12px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] flex items-center gap-2">
                        <ClipboardCheck size={14} strokeWidth={3} /> LOGISTICS {checklistDone}/{CHECKLIST_ITEMS.length}
                      </h3>
                      <button
                        onClick={handleSaveDetails}
                        disabled={savingDealId === selectedDeal.id}
                        className="px-2 py-1 bg-[var(--color-neon-yellow)] text-black border-2 border-black rounded-lg text-[10px] font-[var(--font-bungee)] flex items-center gap-1 disabled:opacity-50"
                      >
                        <Save size={11} strokeWidth={3} /> SAVE
                      </button>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {CHECKLIST_ITEMS.map(([key, label]) => (
                        <button
                          key={key}
                          onClick={() => handleChecklistToggle(key, !checklist[key])}
                          className={`px-2 py-2 rounded-lg border-2 text-[11px] font-bold font-[var(--font-space)] uppercase flex items-center gap-1.5 ${
                            checklist[key]
                              ? "bg-[var(--color-neon-green)] text-black border-[var(--color-neon-green)]"
                              : "bg-zinc-900 text-zinc-400 border-zinc-700"
                          }`}
                        >
                          <Check size={12} strokeWidth={3} /> {label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="bg-black border-4 border-black rounded-xl p-3">
                    <h3 className="text-[12px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] flex items-center gap-2 mb-2">
                      <Clock size={14} strokeWidth={3} /> REMINDERS
                    </h3>
                    <div className="space-y-2">
                      {(selectedDeal.pipeline_reminders || []).map((item: any, idx: number) => (
                        <div key={`${item.text}-${idx}`} className="flex items-start gap-2 text-[12px] leading-snug text-zinc-200 font-[var(--font-space)]">
                          <AlertTriangle size={13} className={item.level === "urgent" ? "text-[var(--color-neon-yellow)]" : "text-[var(--color-neon-green)]"} strokeWidth={3} />
                          <span>{item.text}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="xl:col-span-2 flex justify-end gap-2">
                  <button
                    onClick={handleSaveDetails}
                    disabled={savingDealId === selectedDeal.id}
                    className="px-4 py-2 bg-white text-black border-4 border-black rounded-xl text-[11px] font-[var(--font-bungee)] flex items-center gap-2 disabled:opacity-50"
                  >
                    <Save size={14} strokeWidth={3} /> SAVE DETAILS
                  </button>
                  <button
                    onClick={handleResolvePerformance}
                    disabled={savingDealId === selectedDeal.id}
                    className="px-4 py-2 bg-[var(--color-neon-green)] text-black border-4 border-black rounded-xl text-[11px] font-[var(--font-bungee)] flex items-center gap-2 disabled:opacity-50"
                  >
                    <NotebookPen size={14} strokeWidth={3} /> RESOLVE PERFORMANCE
                  </button>
                </div>
              </div>
            ) : (
              <p className="p-5 text-zinc-500 text-[13px] font-[var(--font-space)] uppercase">SELECT A SECURED DEAL.</p>
            )}
          </section>

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
              <div className="flex flex-wrap items-center justify-end gap-2">
                {rebookNotice && (
                  <span className="bg-black border-2 border-[var(--color-neon-green)] text-[var(--color-neon-green)] px-3 py-1 rounded-full text-[10px] font-bold font-[var(--font-space)] uppercase">
                    {rebookNotice}
                  </span>
                )}
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
            </div>
            {rebookTargets.length === 0 ? (
              <div className="bg-black border-2 border-[var(--color-neon-yellow)]/40 rounded-xl p-4">
                <p className="text-[12px] text-zinc-400 font-[var(--font-space)] uppercase leading-relaxed">
                  COMPLETED PERFORMANCES READY FOR REBOOK WILL APPEAR HERE.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-3">
                {rebookTargets.map((target: any) => (
                  <RebookCard
                    key={target.id}
                    id={target.id}
                    venueName={target.venue_name}
                    note={target.post_show_notes || target.show_summary || "Completed show is ready for a rebook outreach draft."}
                    selected={selectedRebooks.has(target.id)}
                    rebooked={rebookedIds.has(target.id)}
                    onToggle={toggleRebook}
                  />
                ))}
              </div>
            )}
          </section>
        </main>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="block text-[10px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] mb-1 uppercase">{label}</span>
      {children}
    </label>
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
