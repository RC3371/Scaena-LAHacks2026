import React from "react";
import { motion } from "motion/react";
import { Send, Edit3, Sparkles, Loader2, Check } from "lucide-react";
import { api, Pitch, Prospect } from "../../api/client";

export function Outreach() {
  const [pitches, setPitches] = React.useState<Pitch[]>([]);
  const [newProspects, setNewProspects] = React.useState<Prospect[]>([]);
  const [activeId, setActiveId] = React.useState<number | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [generating, setGenerating] = React.useState(false);
  const [sending, setSending] = React.useState<number | null>(null);
  const [recordingFor, setRecordingFor] = React.useState<number | null>(null);

  React.useEffect(() => {
    Promise.all([api.pitches(), api.prospects("new")])
      .then(([p, np]) => {
        setPitches(p);
        setNewProspects(np);
        if (p.length > 0) setActiveId(p[0].id);
      })
      .finally(() => setLoading(false));
  }, []);

  const activePitch = pitches.find(p => p.id === activeId) ?? pitches[0] ?? null;
  const draftCount = pitches.filter(p => p.status === "draft").length;

  async function handleGenerate() {
    if (newProspects.length === 0) return;
    setGenerating(true);
    try {
      const ids = newProspects.slice(0, 5).map(p => p.id);
      const result = await api.generatePitches(ids);
      setPitches(prev => [...result.pitches, ...prev]);
      if (!activeId && result.pitches.length > 0) setActiveId(result.pitches[0].id);
      const updated = await api.prospects("new");
      setNewProspects(updated);
    } catch {}
    finally { setGenerating(false); }
  }

  async function handleSendAll() {
    const ids = pitches.filter(p => p.status === "draft").map(p => p.id);
    if (!ids.length) return;
    setSending(-1);
    try {
      await api.sendPitches(ids);
      setPitches(prev => prev.map(p => ids.includes(p.id) ? { ...p, status: "sent" } : p));
    } catch {}
    finally { setSending(null); }
  }

  async function handleSendOne(pitchId: number) {
    setSending(pitchId);
    try {
      await api.sendPitches([pitchId]);
      setPitches(prev => prev.map(p => p.id === pitchId ? { ...p, status: "sent" } : p));
    } catch {}
    finally { setSending(null); }
  }

  async function handleBook(pitchId: number, prospectId: number) {
    setRecordingFor(pitchId);
    try {
      await api.recordResponse(pitchId, prospectId, "booked");
      setPitches(prev => prev.map(p => p.id === pitchId ? { ...p, status: "booked" } : p));
    } catch {}
    finally { setRecordingFor(null); }
  }

  return (
    <div className="space-y-8 pb-12 h-full flex flex-col">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6"
      >
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-2">Submissions</h1>
          <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">
            Draft, review, and send proposals
          </p>
        </div>
        <div className="flex gap-3">
          {newProspects.length > 0 && (
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="group px-6 py-3 bg-white border border-slate-200 text-slate-700 text-sm font-bold uppercase tracking-wider rounded-md hover:border-[#37afef] hover:text-[#37afef] transition-colors duration-200 flex items-center gap-2 shadow-sm disabled:opacity-50"
            >
              {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} strokeWidth={2.5} />}
              <span>{generating ? "Generating..." : `Generate (${newProspects.length} new)`}</span>
            </button>
          )}
          {draftCount > 0 && (
            <button
              onClick={handleSendAll}
              disabled={sending === -1}
              className="group px-6 py-3 bg-[#37afef] text-white text-sm font-bold uppercase tracking-wider rounded-md hover:bg-[#2998d6] transition-colors duration-200 flex items-center gap-2 shadow-sm shadow-[#37afef]/20 disabled:opacity-50"
            >
              {sending === -1 ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} strokeWidth={2.5} />}
              <span>Dispatch All ({draftCount})</span>
            </button>
          )}
        </div>
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-6 h-6 border-2 border-[#37afef] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : pitches.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-16 text-center">
          <p className="text-slate-900 font-bold text-lg mb-2">No pitches yet</p>
          <p className="text-slate-500 text-sm">Click "Generate" to create personalized pitches for your {newProspects.length} prospects.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1 min-h-[500px]">
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="bg-white border border-slate-200 rounded-lg shadow-sm flex flex-col overflow-hidden"
          >
            <div className="px-5 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50/50">
              <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Draft Queue</h2>
              <span className="text-[10px] bg-slate-200 text-slate-700 font-bold px-2 py-0.5 rounded uppercase tracking-wider">
                {draftCount} Draft{draftCount !== 1 ? "s" : ""}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {pitches.map((pitch) => (
                <button
                  key={pitch.id}
                  onClick={() => setActiveId(pitch.id)}
                  className={`w-full text-left p-4 transition-all duration-200 rounded-md ${
                    activeId === pitch.id
                      ? "bg-[#37afef]/5 border border-[#37afef]/30 shadow-sm"
                      : "bg-transparent border border-transparent hover:bg-slate-50"
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className={`text-base font-bold tracking-tight truncate max-w-[140px] ${activeId === pitch.id ? "text-[#37afef]" : "text-slate-900"}`}>
                      {pitch.prospect_name ?? `Pitch #${pitch.id}`}
                    </h3>
                    {pitch.status === "booked" && <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5 shrink-0" />}
                    {pitch.status === "sent" && <div className="w-2 h-2 rounded-full bg-[#37afef] mt-1.5 shrink-0" />}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-500 font-medium capitalize">{pitch.status}</span>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-sm bg-slate-100 text-slate-500">
                      ${pitch.proposed_rate}/show
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </motion.div>

          {activePitch && (
            <motion.div
              key={activeId}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="lg:col-span-2 bg-white border border-slate-200 rounded-lg shadow-sm flex flex-col relative"
            >
              <div className="p-8 pb-6 flex justify-between items-start border-b border-slate-100">
                <div>
                  <h2 className="text-2xl font-extrabold text-slate-900 mb-1">{activePitch.prospect_name ?? activePitch.subject}</h2>
                  <p className="text-sm font-semibold text-slate-500 tracking-wide">{activePitch.venue_type} · {activePitch.venue_location}</p>
                </div>
                <div className={`text-xs font-bold px-3 py-1.5 rounded capitalize ${
                  activePitch.status === "booked" ? "bg-emerald-100 text-emerald-700"
                  : activePitch.status === "sent" ? "bg-[#37afef]/10 text-[#37afef]"
                  : "bg-slate-100 text-slate-500"
                }`}>{activePitch.status}</div>
              </div>

              <div className="px-8 py-4 bg-amber-50 border-b border-amber-100 flex gap-3 items-start">
                <Sparkles className="text-amber-500 shrink-0 mt-0.5" size={18} strokeWidth={2.5} />
                <div>
                  <span className="text-amber-700 text-xs font-bold tracking-wider uppercase mb-1 block">Subject line:</span>
                  <p className="text-sm text-amber-900 font-medium leading-relaxed">{activePitch.subject}</p>
                </div>
              </div>

              <div className="flex-1 p-8 bg-slate-50/50 overflow-y-auto">
                <div className="w-full h-full bg-transparent text-slate-700 text-[15px] leading-loose whitespace-pre-wrap outline-none font-medium cursor-text font-serif">
                  {activePitch.body}
                </div>
              </div>

              <div className="px-8 py-5 flex justify-between items-center border-t border-slate-200 bg-white rounded-b-lg">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                  ${activePitch.proposed_rate}/show
                </span>
                <div className="flex gap-3">
                  {activePitch.status === "draft" && (
                    <button
                      onClick={() => handleSendOne(activePitch.id)}
                      disabled={sending === activePitch.id}
                      className="px-6 py-2.5 bg-slate-900 rounded text-xs font-bold text-white transition-colors tracking-widest uppercase hover:bg-[#37afef] shadow-sm disabled:opacity-50 flex items-center gap-2"
                    >
                      {sending === activePitch.id ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
                      Dispatch
                    </button>
                  )}
                  {activePitch.status === "sent" && (
                    <button
                      onClick={() => handleBook(activePitch.id, activePitch.prospect_id)}
                      disabled={recordingFor === activePitch.id}
                      className="px-6 py-2.5 bg-emerald-600 rounded text-xs font-bold text-white transition-colors tracking-widest uppercase hover:bg-emerald-700 shadow-sm disabled:opacity-50 flex items-center gap-2"
                    >
                      {recordingFor === activePitch.id ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                      Mark Booked
                    </button>
                  )}
                  {activePitch.status === "booked" && (
                    <span className="px-6 py-2.5 bg-emerald-50 border border-emerald-200 rounded text-xs font-bold text-emerald-700 tracking-widest uppercase">
                      Confirmed
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  );
}
