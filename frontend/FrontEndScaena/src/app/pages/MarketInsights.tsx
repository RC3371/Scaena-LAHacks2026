import React from "react";
import { motion } from "motion/react";
import { Compass, Sparkles, Loader2 } from "lucide-react";
import { api, Prospect } from "../../api/client";

export function MarketInsights() {
  const [research, setResearch] = React.useState<any>(null);
  const [prospects, setProspects] = React.useState<Prospect[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [scanning, setScanning] = React.useState(false);

  React.useEffect(() => {
    Promise.all([
      api.marketResearch().catch(() => null),
      api.prospects(),
    ]).then(([r, p]) => {
      setResearch(r?.data ?? null);
      setProspects(p);
    }).finally(() => setLoading(false));
  }, []);

  async function handleScan() {
    setScanning(true);
    try {
      const result = await api.runMarketResearch();
      setResearch(result.data ?? null);
      const p = await api.prospects();
      setProspects(p);
    } catch {}
    finally { setScanning(false); }
  }

  const mi = research?.market_insights;
  const ca = research?.competitive_analysis;

  const tableProspects = prospects.slice(0, 8);

  return (
    <div className="space-y-8 pb-12">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6"
      >
        <div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight mb-2">Market Insights</h1>
          <p className="text-slate-500 text-sm font-semibold tracking-wide uppercase">
            Analyze rates, fees, and opportunities
          </p>
        </div>
        <button
          onClick={handleScan}
          disabled={scanning}
          className="group px-6 py-3 bg-white border border-slate-200 text-slate-700 text-sm font-bold uppercase tracking-wider rounded-md hover:border-[#37afef] hover:text-[#37afef] transition-colors duration-200 flex items-center gap-2 shadow-sm disabled:opacity-50"
        >
          {scanning
            ? <Loader2 size={16} className="animate-spin" />
            : <Compass size={16} strokeWidth={2.5} className="group-hover:rotate-45 transition-transform duration-300" />}
          <span>{scanning ? "Scanning..." : "Execute Scan"}</span>
        </button>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="lg:col-span-2 bg-white border border-slate-200 p-8 rounded-lg shadow-sm flex flex-col justify-between"
        >
          <div>
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Fee Analysis</h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-5 bg-slate-50 rounded-md border border-slate-100">
                <p className="text-xs text-slate-500 uppercase font-bold mb-2">Entry Level</p>
                <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
                  {loading ? "—" : mi?.market_rates?.entry_level ?? "—"}
                </p>
              </div>
              <div className="p-5 bg-[#37afef]/5 border border-[#37afef]/30 rounded-md relative">
                <p className="text-xs uppercase font-bold mb-2 flex items-center justify-between text-[#37afef]">
                  Mid Level
                  <span className="px-1.5 py-0.5 bg-[#37afef] text-white text-[9px] rounded-sm">YOU</span>
                </p>
                <p className="text-3xl font-extrabold text-[#37afef] tracking-tight">
                  {loading ? "—" : `$${mi?.recommended_rate_min ?? "?"}–$${mi?.recommended_rate_max ?? "?"}`}
                  <span className="text-sm text-[#37afef]/70 font-semibold tracking-normal">/show</span>
                </p>
              </div>
              <div className="p-5 bg-slate-50 rounded-md border border-slate-100">
                <p className="text-xs text-slate-500 uppercase font-bold mb-2">Established</p>
                <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
                  {loading ? "—" : mi?.market_rates?.established ?? "—"}
                </p>
              </div>
            </div>
          </div>

          {mi && (
            <div className="mt-6 flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-md">
              <Sparkles className="text-amber-500 shrink-0 mt-0.5" size={18} strokeWidth={2.5} />
              <p className="text-sm font-medium text-slate-700 leading-relaxed">
                <span className="font-bold text-amber-700 uppercase text-xs tracking-wider mr-2">Strategic Note:</span>
                {mi.pricing_recommendation}
              </p>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="bg-white border border-slate-200 p-8 rounded-lg shadow-sm flex flex-col"
        >
          <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Market Position</h2>
          <div className="space-y-6 flex-1 flex flex-col justify-center">
            <div className="flex justify-between items-end border-b border-slate-100 pb-3">
              <span className="text-sm text-slate-500 font-semibold">Similar Works</span>
              <span className="text-2xl font-extrabold text-slate-900">{loading ? "—" : ca?.similar_entertainers_count ?? "—"}</span>
            </div>
            <div className="flex justify-between items-end border-b border-slate-100 pb-3">
              <span className="text-sm text-slate-500 font-semibold">Market Avg</span>
              <span className="text-2xl font-extrabold text-slate-900">${loading ? "—" : ca?.average_market_rate ?? "—"}</span>
            </div>
            <div className="flex justify-between items-end border-b border-[#37afef]/20 pb-3">
              <span className="text-sm text-[#37afef] font-bold">Your Rate</span>
              <span className="text-2xl font-extrabold text-[#37afef]">${loading ? "—" : ca?.your_current_rate ?? "—"}</span>
            </div>
            <div className="text-xs text-slate-400 font-semibold capitalize">
              Positioning: {loading ? "—" : ca?.positioning ?? "—"}
            </div>
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.4 }}
        className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden"
      >
        <div className="p-6 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">Curated Opportunities</h2>
          <span className="text-xs text-slate-400 font-semibold">{prospects.length} venues in pipeline</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm whitespace-nowrap">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Venue / Organization</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Classification</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Location</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Est. Fee</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest">Status</th>
                <th className="px-6 py-4 text-xs font-bold text-slate-400 uppercase tracking-widest text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 6 }).map((_, j) => (
                        <td key={j} className="px-6 py-4"><div className="h-4 bg-slate-100 rounded animate-pulse w-24" /></td>
                      ))}
                    </tr>
                  ))
                : tableProspects.map((venue, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition-colors group">
                      <td className="px-6 py-4 text-slate-900 font-bold">{venue.name}</td>
                      <td className="px-6 py-4">
                        <span className="border border-slate-200 px-2 py-1 rounded bg-white text-xs font-semibold text-slate-600">{venue.type}</span>
                      </td>
                      <td className="px-6 py-4 text-slate-600 font-medium">{venue.location}</td>
                      <td className="px-6 py-4 text-slate-900 font-bold">${venue.typical_pay_min}–${venue.typical_pay_max}</td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded capitalize ${
                          venue.status === "booked" ? "bg-emerald-100 text-emerald-700"
                          : venue.status === "pitched" ? "bg-[#37afef]/10 text-[#37afef]"
                          : venue.status === "responded" ? "bg-indigo-100 text-indigo-700"
                          : "bg-slate-100 text-slate-500"
                        }`}>{venue.status}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={`text-xs font-bold text-white px-4 py-2 rounded ${
                          venue.status === "new" ? "bg-slate-800 group-hover:bg-[#37afef]" : "bg-slate-200 text-slate-500"
                        } transition-colors`}>
                          {venue.status === "new" ? "Queue" : venue.status}
                        </span>
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
