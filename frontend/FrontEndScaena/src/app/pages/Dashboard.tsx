import React from "react";
import { motion } from "motion/react";
import { ArrowUpRight, Zap, Target, Mail, BarChart3, Star } from "lucide-react";
import { api, Analytics, Response } from "../../api/client";

export function Dashboard() {
  const [analytics, setAnalytics] = React.useState<Analytics | null>(null);
  const [responses, setResponses] = React.useState<Response[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    Promise.all([api.analytics(), api.responses()])
      .then(([a, r]) => { setAnalytics(a); setResponses(r); })
      .finally(() => setLoading(false));
  }, []);

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05 } }
  };
  const item = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  const s = analytics?.summary;
  const stats = [
    { label: "Active Proposals", value: loading ? "—" : String(s?.total_pitches_sent ?? 0).padStart(2, "0"), icon: Target, trend: `${s?.overall_response_rate ?? 0}% response` },
    { label: "Responses", value: loading ? "—" : String(s?.total_responses ?? 0).padStart(2, "0"), icon: Mail, trend: `+${s?.interested_leads ?? 0} interested` },
    { label: "Secured Runs", value: loading ? "—" : String(s?.total_bookings ?? 0).padStart(2, "0"), icon: Star, trend: "confirmed bookings" },
    { label: "Est. Revenue", value: loading ? "—" : `$${((s?.total_bookings ?? 0) * (s?.avg_proposed_rate ?? 0)).toLocaleString()}`, icon: BarChart3, trend: `@ $${s?.avg_proposed_rate ?? 0}/show` },
  ];

  const agentStatus = [
    { name: "Discovery Engine", status: analytics ? "Active" : "Idle", dot: analytics ? "bg-[#37afef]" : "bg-slate-300" },
    { name: "Submission Sync", status: (s?.total_pitches_sent ?? 0) > 0 ? "Active" : "Idle", dot: (s?.total_pitches_sent ?? 0) > 0 ? "bg-[#37afef]" : "bg-slate-300" },
    { name: "Data Analytics", status: analytics?.ai_insights ? "Processed" : "Processing", dot: analytics?.ai_insights ? "bg-[#37afef]" : "bg-amber-400" },
    { name: "Follow-up Queue", status: (s?.follow_ups_sent ?? 0) > 0 ? "Active" : "Standby", dot: (s?.follow_ups_sent ?? 0) > 0 ? "bg-[#37afef]" : "bg-slate-300" },
  ];

  const recentActivity = responses.slice(0, 4).map(r => ({
    time: new Date(r.responded_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    text: `${r.venue_name} ${r.response_type === "booked" ? "confirmed booking" : r.response_type === "interested" ? "responded — interested" : r.response_type === "negotiating" ? "is negotiating rate" : "responded to proposal"}`,
    highlight: r.response_type === "booked" || r.response_type === "interested",
  }));

  if (recentActivity.length === 0) {
    recentActivity.push(
      { time: "—", text: "No responses yet — send pitches to get started", highlight: false },
    );
  }

  async function handleSync() {
    try {
      const result = await api.runAnalytics();
      setAnalytics(result);
    } catch {}
  }

  return (
    <div className="space-y-8 pb-12">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6"
      >
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-2">Curtain Call</h1>
          <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">
            Stage Management & Automated Submissions
          </p>
        </div>
        <button
          onClick={handleSync}
          className="group px-6 py-3 bg-[#37afef] text-white text-sm font-bold uppercase tracking-wider rounded-md hover:bg-[#2998d6] transition-colors duration-200 flex items-center gap-2 shadow-sm shadow-[#37afef]/20"
        >
          <Zap size={16} strokeWidth={2.5} />
          <span>Execute Sync</span>
        </button>
      </motion.div>

      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {stats.map((stat, i) => (
          <motion.div
            key={i}
            variants={item}
            className="bg-white border border-slate-200 p-6 rounded-lg shadow-sm flex flex-col justify-between"
          >
            <div className="flex justify-between items-start mb-6">
              <div className="p-2 bg-slate-50 rounded-md border border-slate-100 text-[#37afef]">
                <stat.icon size={20} strokeWidth={2.5} />
              </div>
              <div className="flex items-center text-xs font-bold text-[#37afef] bg-[#37afef]/10 px-2 py-1 rounded">
                <ArrowUpRight size={14} className="mr-1" strokeWidth={2.5} />
                {stat.trend}
              </div>
            </div>
            <div>
              <p className="text-3xl font-extrabold text-slate-900 tracking-tight mb-1">{stat.value}</p>
              <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">{stat.label}</p>
            </div>
          </motion.div>
        ))}
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="flex flex-col gap-4"
        >
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Subsystem Status</h2>
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            {agentStatus.map((agent, i) => (
              <div key={i} className="flex items-center justify-between p-4 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${agent.dot}`} />
                  <span className="text-sm font-bold text-slate-700">{agent.name}</span>
                </div>
                <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">{agent.status}</span>
              </div>
            ))}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.4 }}
          className="flex flex-col gap-4"
        >
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest">Recent Actions</h2>
          <div className="bg-white border border-slate-200 p-6 rounded-lg shadow-sm space-y-6">
            {recentActivity.map((activity, i) => (
              <div key={i} className="flex gap-4 items-start relative">
                <div className="flex flex-col items-center mt-1">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${activity.highlight ? "bg-[#37afef]" : "bg-slate-300"}`} />
                  {i !== recentActivity.length - 1 && <div className="w-px h-10 bg-slate-200 mt-2" />}
                </div>
                <div className="-mt-0.5">
                  <p className={`text-sm font-semibold ${activity.highlight ? "text-slate-900" : "text-slate-600"}`}>{activity.text}</p>
                  <p className="text-xs font-semibold text-slate-400 mt-1">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {analytics?.ai_insights && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.4 }}
          className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex"
        >
          <div className="w-1.5 bg-[#37afef]" />
          <div className="flex-1 p-6">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Agent 3 — Strategic Insight</p>
            <p className="text-slate-800 font-semibold text-sm leading-relaxed">{analytics.ai_insights.top_insight}</p>
            <div className="flex flex-wrap gap-2 mt-3">
              {analytics.ai_insights.focus_channels.map(c => (
                <span key={c} className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 bg-[#37afef]/10 text-[#37afef] rounded">{c}</span>
              ))}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
