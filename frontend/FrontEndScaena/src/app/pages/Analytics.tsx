import React from "react";
import { motion } from "motion/react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, LineChart, Line, CartesianGrid } from "recharts";
import { Drama, Loader2, RefreshCw } from "lucide-react";
import { api, Analytics as AnalyticsType, TrendPoint } from "../../api/client";

const COLORS = ["#37afef", "#0ea5e9", "#bae6fd", "#7dd3fc", "#38bdf8"];

export function Analytics() {
  const [analytics, setAnalytics] = React.useState<AnalyticsType | null>(null);
  const [trend, setTrend] = React.useState<TrendPoint[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [running, setRunning] = React.useState(false);

  React.useEffect(() => {
    Promise.all([api.analytics(), api.analyticsTrend()])
      .then(([a, t]) => { setAnalytics(a); setTrend(t); })
      .finally(() => setLoading(false));
  }, []);

  async function handleRun() {
    setRunning(true);
    try {
      const [a, t] = await Promise.all([api.runAnalytics(), api.analyticsTrend()]);
      setAnalytics(a);
      setTrend(t);
    } catch {}
    finally { setRunning(false); }
  }

  const venueData = analytics?.venue_performance
    ? Object.entries(analytics.venue_performance)
        .filter(([, v]) => v.sent > 0)
        .map(([name, v]) => ({
          name: name.replace(" Event", "").replace(" Venue", "").substring(0, 10),
          rate: v.response_rate,
        }))
    : [];

  const angleData = analytics?.ai_insights?.effective_angles?.map((a, i) => ({
    name: a.split(" ").slice(0, 3).join(" "),
    value: 60 - i * 8,
  })) ?? [
    { name: "Video Proof", value: 60 },
    { name: "Recent Acts", value: 50 },
    { name: "Audience Fit", value: 40 },
  ];

  const trendData = trend.map((t, i) => ({
    week: `Wk ${i + 1}`,
    rate: t.overall_response_rate,
    bookings: t.total_bookings,
  }));

  const s = analytics?.summary;

  return (
    <div className="space-y-8 pb-12">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6"
      >
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-2">Performance Analytics</h1>
          <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">
            Review historical submission success
          </p>
        </div>
        <button
          onClick={handleRun}
          disabled={running}
          className="group px-6 py-3 bg-white border border-slate-200 text-slate-700 text-sm font-bold uppercase tracking-wider rounded-md hover:border-[#37afef] hover:text-[#37afef] transition-colors duration-200 shadow-sm disabled:opacity-50 flex items-center gap-2"
        >
          {running ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          Run Analysis
        </button>
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-6 h-6 border-2 border-[#37afef] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Pitches Sent", value: s?.total_pitches_sent ?? 0, color: "text-slate-900" },
              { label: "Response Rate", value: `${s?.overall_response_rate ?? 0}%`, color: "text-[#37afef]" },
              { label: "Shows Booked", value: s?.total_bookings ?? 0, color: "text-emerald-600" },
              { label: "Avg Rate", value: `$${s?.avg_proposed_rate ?? 0}`, color: "text-slate-900" },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-white border border-slate-200 rounded-lg shadow-sm p-5">
                <p className="text-xs text-slate-400 uppercase font-bold tracking-widest mb-1">{label}</p>
                <p className={`text-3xl font-extrabold tracking-tight ${color}`}>{value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.4 }}
              className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 h-[340px] flex flex-col"
            >
              <h2 className="text-sm font-bold tracking-widest text-slate-500 uppercase mb-6">Conversion Matrix</h2>
              <div className="flex-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={venueData.length > 0 ? venueData : [{ name: "No data", rate: 0 }]} layout="vertical" margin={{ left: 0, right: 0 }}>
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" stroke="#64748b" width={80} tickLine={false} axisLine={false} fontSize={12} fontFamily="inherit" fontWeight="600" />
                    <Tooltip
                      cursor={{ fill: "#f1f5f9" }}
                      contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "6px", fontSize: "13px", color: "#0f172a", fontWeight: "bold" }}
                      itemStyle={{ color: "#37afef" }}
                      formatter={(v: any) => [`${v}%`, "Response Rate"]}
                    />
                    <Bar dataKey="rate" fill="#37afef" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.4 }}
              className="bg-white border border-slate-200 rounded-lg shadow-sm p-6 h-[340px] flex flex-col"
            >
              <h2 className="text-sm font-bold tracking-widest text-slate-500 uppercase mb-6">
                {trendData.length > 1 ? "Performance Trend" : "Effective Angles"}
              </h2>
              <div className="flex-1">
                {trendData.length > 1 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData} margin={{ left: -20, right: 0, top: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis dataKey="week" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "6px", fontSize: "13px", fontWeight: "bold" }}
                      />
                      <Line type="monotone" dataKey="rate" stroke="#37afef" strokeWidth={2.5} dot={{ fill: "#37afef", r: 4 }} name="Response Rate %" />
                      <Line type="monotone" dataKey="bookings" stroke="#10b981" strokeWidth={2.5} dot={{ fill: "#10b981", r: 4 }} name="Bookings" />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={angleData} cx="50%" cy="50%" innerRadius={70} outerRadius={100} paddingAngle={4} dataKey="value" stroke="none">
                        {angleData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: "#ffffff", border: "1px solid #e2e8f0", borderRadius: "6px", fontSize: "13px", fontWeight: "bold" }} />
                    </PieChart>
                  </ResponsiveContainer>
                )}
              </div>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.4 }}
            className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden flex"
          >
            <div className="w-1.5 bg-[#37afef]" />
            <div className="flex-1">
              <div className="px-8 py-5 border-b border-slate-100 flex items-center gap-3 bg-slate-50/50">
                <Drama size={20} className="text-[#37afef]" strokeWidth={2.5} />
                <h2 className="text-sm font-bold tracking-widest text-slate-900 uppercase">Directorial Strategy</h2>
              </div>

              <div className="p-8 sm:p-10 grid grid-cols-1 md:grid-cols-3 gap-10">
                <div className="md:col-span-2">
                  <div className="text-sm text-slate-700 leading-relaxed font-medium">
                    <span className="text-slate-400 font-bold text-xs tracking-widest uppercase mb-3 block">Analysis Summary</span>
                    {analytics?.ai_insights ? (
                      <>
                        {analytics.ai_insights.top_insight}
                        <br /><br />
                        <span className="inline-block border-l-4 border-[#37afef] pl-4 italic text-slate-500 mt-1">
                          {analytics.ai_insights.rate_analysis?.reasoning ?? "Continue optimizing your pitch angles for higher conversion."}
                        </span>
                        <div className="mt-4 space-y-2">
                          {analytics.ai_insights.recommendations.slice(0, 2).map((r, i) => (
                            <div key={i} className="flex items-start gap-2 text-sm">
                              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 mt-0.5 ${r.priority === "high" ? "bg-rose-100 text-rose-700" : "bg-amber-100 text-amber-700"}`}>{r.priority}</span>
                              <span className="text-slate-600">{r.action}</span>
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <>
                        {venueData.length > 0
                          ? `${venueData[0]?.name} venues are maintaining the highest response rates. Recommended action: focus next round of submissions on this channel.`
                          : "Send pitches and record responses to generate AI strategy recommendations."}
                        <br /><br />
                        <span className="inline-block border-l-4 border-[#37afef] pl-4 italic text-slate-500 mt-1">
                          Run Analysis to get Claude-powered directorial strategy.
                        </span>
                      </>
                    )}
                  </div>
                  <button
                    onClick={handleRun}
                    disabled={running}
                    className="mt-8 text-xs uppercase tracking-wider text-white font-bold bg-slate-900 rounded px-6 py-3 hover:bg-[#37afef] transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
                  >
                    {running ? <Loader2 size={12} className="animate-spin" /> : null}
                    Update Agent Directives
                  </button>
                </div>

                <div className="space-y-8 flex flex-col justify-center border-t md:border-t-0 md:border-l border-slate-100 pt-8 md:pt-0 md:pl-10">
                  <div>
                    <p className="text-xs text-slate-400 uppercase tracking-widest font-bold mb-1">Avg Rate</p>
                    <p className="text-4xl text-slate-900 font-extrabold tracking-tight">${s?.avg_proposed_rate ?? "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 uppercase tracking-widest font-bold mb-1">Success Rate</p>
                    <p className="text-4xl text-[#37afef] font-extrabold tracking-tight">{s?.overall_response_rate ?? "—"}%</p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </div>
  );
}
