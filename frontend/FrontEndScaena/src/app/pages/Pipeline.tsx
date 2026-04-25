import React from "react";
import { motion } from "motion/react";
import { PlayCircle, AlertTriangle, ScrollText, Loader2, Check, X } from "lucide-react";
import { api, FollowUp } from "../../api/client";

export function Pipeline() {
  const [followUps, setFollowUps] = React.useState<FollowUp[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [generating, setGenerating] = React.useState(false);
  const [sending, setSending] = React.useState<number | null>(null);

  React.useEffect(() => {
    api.followups()
      .then(setFollowUps)
      .finally(() => setLoading(false));
  }, []);

  async function handleExecute() {
    setGenerating(true);
    try {
      await api.generateFollowups();
      const updated = await api.followups();
      setFollowUps(updated);
    } catch {}
    finally { setGenerating(false); }
  }

  async function handleSend(id: number) {
    setSending(id);
    try {
      await api.sendFollowup(id);
      setFollowUps(prev => prev.map(f => f.id === id ? { ...f, status: "sent" } : f));
    } catch {}
    finally { setSending(null); }
  }

  async function handleCancel(id: number) {
    await api.cancelFollowup(id);
    setFollowUps(prev => prev.map(f => f.id === id ? { ...f, status: "cancelled" } : f));
  }

  const now = new Date();
  const active = followUps.filter(f => f.status === "scheduled" || f.status === "sent").slice(0, 6);
  const due = followUps.filter(f => f.status === "scheduled" && new Date(f.scheduled_for) <= now);
  const pendingCount = followUps.filter(f => f.status === "scheduled").length;

  const seqLabel: Record<number, string> = {
    1: "Send Reel / Video Proof",
    2: "Send Social Proof",
    3: "Final Reach Out",
  };

  return (
    <div className="space-y-8 pb-12">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6"
      >
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-2">The Pipeline</h1>
          <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">
            Automated relationship management
          </p>
        </div>
        <button
          onClick={handleExecute}
          disabled={generating}
          className="group px-6 py-3 bg-white border border-slate-200 text-slate-700 text-sm font-bold uppercase tracking-wider rounded-md hover:border-[#37afef] hover:text-[#37afef] transition-colors duration-200 flex items-center gap-2 shadow-sm disabled:opacity-50"
        >
          {generating ? <Loader2 size={18} className="animate-spin" strokeWidth={2.5} /> : <PlayCircle size={18} strokeWidth={2.5} />}
          <span>{generating ? "Generating..." : "Execute Sequence"}</span>
        </button>
      </motion.div>

      {due.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-amber-50 border border-amber-200 rounded-lg px-6 py-4 flex items-center justify-between"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle size={18} className="text-amber-500" strokeWidth={2.5} />
            <p className="text-sm font-bold text-amber-900">
              {due.length} follow-up{due.length !== 1 ? "s" : ""} ready to send — venues are waiting
            </p>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 bg-amber-200 text-amber-800 rounded">Action Required</span>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="bg-white border border-slate-200 rounded-lg shadow-sm flex flex-col"
        >
          <div className="p-6 border-b border-slate-200 bg-slate-50/50 rounded-t-lg flex justify-between items-center">
            <div className="flex items-center gap-2.5">
              <ScrollText className="text-[#37afef]" size={20} strokeWidth={2.5} />
              <h2 className="text-sm font-bold tracking-widest text-slate-600 uppercase">Active Routes</h2>
            </div>
            <span className="text-[10px] text-[#37afef] bg-[#37afef]/10 px-2 py-1 rounded font-bold uppercase tracking-wider">
              {pendingCount} Pending
            </span>
          </div>

          <div className="p-8 flex-1">
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <div className="w-6 h-6 border-2 border-[#37afef] border-t-transparent rounded-full animate-spin" />
              </div>
            ) : active.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-slate-500 font-semibold text-sm">No follow-ups scheduled yet</p>
                <p className="text-slate-400 text-xs mt-1">Click "Execute Sequence" to generate them</p>
              </div>
            ) : (
              <div className="relative space-y-8 before:absolute before:inset-0 before:ml-4 before:-translate-x-px before:h-full before:w-0.5 before:bg-gradient-to-b before:from-[#37afef] before:via-slate-200 before:to-transparent">
                {active.map((item, i) => {
                  const isDue = new Date(item.scheduled_for) <= now && item.status === "scheduled";
                  return (
                    <div key={item.id} className="relative flex items-start gap-4">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full border-2 border-white bg-slate-200 shrink-0 z-10 shadow-sm mt-1">
                        <div className={`w-3 h-3 rounded-full ${item.status === "sent" ? "bg-slate-400" : isDue ? "bg-amber-400" : "bg-[#37afef]"}`} />
                      </div>
                      <div className={`flex-1 p-5 bg-white border rounded-lg shadow-sm transition-colors ${isDue ? "border-amber-300" : "border-slate-200 hover:border-[#37afef]"}`}>
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="text-base font-bold text-slate-900 tracking-tight truncate max-w-[180px]">{item.prospect_name}</h3>
                          <span className="text-sm font-bold text-[#37afef] shrink-0 ml-2">#{item.sequence_number}</span>
                        </div>
                        <div className="text-sm text-slate-600 mb-4 font-medium">
                          <span className="text-[#37afef] font-bold">Day {item.sequence_number === 1 ? 3 : item.sequence_number === 2 ? 7 : 14}</span>
                          <span className="mx-2 text-slate-300">•</span>
                          {seqLabel[item.sequence_number] ?? item.subject}
                        </div>
                        {item.status === "scheduled" ? (
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleSend(item.id)}
                              disabled={sending === item.id}
                              className="flex-1 text-xs uppercase tracking-wider font-bold text-white bg-slate-800 rounded py-2.5 hover:bg-[#37afef] transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-1.5"
                            >
                              {sending === item.id ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                              Review & Send
                            </button>
                            <button
                              onClick={() => handleCancel(item.id)}
                              className="px-3 py-2.5 text-slate-400 hover:text-red-400 border border-slate-200 rounded transition-colors"
                            >
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <div className="w-full text-xs uppercase tracking-wider font-bold text-slate-500 bg-slate-50 border border-slate-200 rounded py-2.5 text-center">
                            Transmitted
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </motion.div>

        <div className="space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="bg-white border border-slate-200 rounded-lg shadow-sm"
          >
            <div className="p-6 border-b border-slate-200 bg-slate-50/50 rounded-t-lg flex items-center gap-2.5">
              <AlertTriangle className="text-rose-500" size={20} strokeWidth={2.5} />
              <h2 className="text-sm font-bold tracking-widest text-slate-600 uppercase">Correspondence Flags</h2>
            </div>
            <div className="p-6">
              <div className="p-6 bg-white border border-slate-200 rounded-lg hover:border-rose-300 transition-colors shadow-sm">
                <div className="flex justify-between items-center mb-5 border-b border-slate-100 pb-4">
                  <h3 className="text-lg font-bold text-slate-900 tracking-tight">No-response venues</h3>
                  <span className="text-[10px] text-rose-700 bg-rose-100 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                    {due.length > 0 ? "Action Needed" : "All Clear"}
                  </span>
                </div>
                <div className="text-sm text-slate-600 mb-5 font-medium">
                  {due.length > 0
                    ? <><span className="text-rose-600 font-bold mr-1 uppercase tracking-widest text-xs">Note:</span> {due.length} venues haven't responded to your pitch</>
                    : <span className="text-slate-400">No urgent flags — pipeline is healthy</span>
                  }
                </div>
                {due.length > 0 && (
                  <div className="p-5 bg-rose-50 border-l-4 border-rose-400 rounded-r-md">
                    <span className="text-xs font-bold text-rose-800 uppercase tracking-widest mb-2 block">Suggested Pivot</span>
                    <p className="text-sm text-rose-950 font-medium leading-relaxed">
                      Send Day-3 follow-ups with your performance reel. Adds video proof shown to increase response rate by 40%.
                    </p>
                    <button
                      onClick={handleExecute}
                      disabled={generating}
                      className="mt-4 w-full text-xs font-bold uppercase tracking-wider text-white bg-rose-500 rounded py-2.5 hover:bg-rose-600 transition-colors shadow-sm disabled:opacity-50"
                    >
                      Execute Sequence
                    </button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            className="bg-white border border-slate-200 rounded-lg shadow-sm p-6"
          >
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Pipeline Stats</h2>
            <div className="space-y-4">
              {[
                { label: "Total Scheduled", value: followUps.filter(f => f.status === "scheduled").length },
                { label: "Sent", value: followUps.filter(f => f.status === "sent").length },
                { label: "Due Now", value: due.length },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                  <span className="text-sm text-slate-500 font-semibold">{label}</span>
                  <span className="text-xl font-extrabold text-slate-900">{value}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
