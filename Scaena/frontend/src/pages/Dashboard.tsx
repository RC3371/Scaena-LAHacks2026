import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "motion/react";
import { ArrowRight, Compass, Send, BarChart2, Zap } from "lucide-react";
import { client } from "../api/client";
import { useWebSocket } from "../hooks/useWebSocket";
import { useAgentEvents } from "../hooks/useAgentEvents";

function statusLabel(status: string) {
  if (status === "working") return "SCANNING SECTOR";
  if (status === "complete") return "SCAN COMPLETE";
  if (status === "error") return "ERROR";
  return "STANDBY";
}

export function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const { events } = useWebSocket();
  const { statuses, latestByAgent } = useAgentEvents(events);

  useEffect(() => {
    (async () => {
      const entertainers = await client.entertainers.active();
      if (!entertainers.length) return;
      const s = await client.analytics.summary(entertainers[0].id);
      setSummary(s);
    })();
  }, []);

  const agent1Label = latestByAgent.agent1?.message || (statuses.agent1 === "working" ? "SCANNING SECTOR" : "STANDBY");
  const agent2Label = latestByAgent.agent2?.message || `${summary?.total_pitches ?? "—"} PITCHES SENT`;
  const agent3Label = latestByAgent.agent3?.message || `RESPONSE RATE ${summary?.response_rate != null ? Math.round(summary.response_rate * 100) + "%" : "—"}`;
  const agent4Label = latestByAgent.agent4?.message || `${summary?.bookings_count ?? "—"} BOOKINGS ACTIVE`;

  return (
    <div className="h-full flex flex-col justify-center max-w-6xl mx-auto pb-10 px-8">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.15 }}
      >
        <div className="bg-[var(--color-neon-purple)] text-white border-4 border-black inline-block px-6 py-2 rounded-full mb-8 font-bold shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] font-[var(--font-space)]">
          SCAENA OS :: {summary ? `${summary.total_pitches} PITCHES // ${Math.min(100, Math.round((summary.response_rate || 0) * 100))}% RESPONSE RATE` : "INITIALIZING..."}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* Agent 1 - Pink */}
          <Link to="/insights" className="group bg-[var(--color-panel-bg)] border-4 border-black p-6 rounded-3xl hover:-translate-y-2 hover:shadow-[8px_8px_0px_0px_var(--color-neon-pink)] transition-all duration-300 ease-out flex flex-col justify-between h-48 shadow-[6px_6px_0px_0px_var(--color-neon-pink)] relative overflow-hidden">
            <div className="absolute -right-4 -bottom-4 opacity-20 transform group-hover:scale-125 group-hover:rotate-12 transition-all duration-300">
              <Compass size={140} color="var(--color-neon-pink)" />
            </div>
            <div className="relative z-10 flex justify-between items-start">
              <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-pink)] bg-black px-4 py-1 rounded-full border-2 border-[var(--color-neon-pink)]">AGENT 1</h2>
              <div className="bg-[var(--color-neon-pink)] p-2 rounded-xl border-2 border-black group-hover:scale-110 transition-transform">
                <ArrowRight size={20} className="text-black" strokeWidth={3} />
              </div>
            </div>
            <div className="relative z-10">
              <p className="text-white font-bold mb-2 text-sm">Market Research</p>
              <div className="flex items-center gap-3 bg-black/50 w-fit px-3 py-2 rounded-xl border-2 border-[var(--color-neon-pink)]">
                <div className={`w-3 h-3 rounded-full bg-[var(--color-neon-pink)] ${statuses.agent1 === "working" ? "animate-ping" : "animate-pulse"}`} />
                <p className="text-[14px] font-bold text-[var(--color-neon-pink)] uppercase font-[var(--font-space)]">{statusLabel(statuses.agent1)}</p>
              </div>
            </div>
          </Link>

          {/* Agent 2 - Cyan */}
          <Link to="/outreach" className="group bg-[var(--color-panel-bg)] border-4 border-black p-6 rounded-3xl hover:-translate-y-2 hover:shadow-[8px_8px_0px_0px_var(--color-neon-cyan)] transition-all duration-300 ease-out flex flex-col justify-between h-48 shadow-[6px_6px_0px_0px_var(--color-neon-cyan)] relative overflow-hidden">
            <div className="absolute -right-4 -bottom-4 opacity-20 transform group-hover:scale-125 group-hover:rotate-12 transition-all duration-300">
              <Send size={140} color="var(--color-neon-cyan)" />
            </div>
            <div className="relative z-10 flex justify-between items-start">
              <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-cyan)] bg-black px-4 py-1 rounded-full border-2 border-[var(--color-neon-cyan)]">AGENT 2</h2>
              <div className="bg-[var(--color-neon-cyan)] p-2 rounded-xl border-2 border-black group-hover:scale-110 transition-transform">
                <ArrowRight size={20} className="text-black" strokeWidth={3} />
              </div>
            </div>
            <div className="relative z-10">
              <p className="text-white font-bold mb-2 text-sm">Outreach Strategy</p>
              <div className="flex items-center gap-3 bg-black/50 w-fit px-3 py-2 rounded-xl border-2 border-[var(--color-neon-cyan)]">
                <div className={`w-3 h-3 rounded-full bg-[var(--color-neon-cyan)] ${statuses.agent2 === "working" ? "animate-ping" : "animate-pulse"}`} />
                <p className="text-[14px] font-bold text-[var(--color-neon-cyan)] uppercase font-[var(--font-space)]">{agent2Label.substring(0, 24)}</p>
              </div>
            </div>
          </Link>

          {/* Agent 3 - Green */}
          <Link to="/analytics" className="group bg-[var(--color-panel-bg)] border-4 border-black p-6 rounded-3xl hover:-translate-y-2 hover:shadow-[8px_8px_0px_0px_var(--color-neon-green)] transition-all duration-300 ease-out flex flex-col justify-between h-48 shadow-[6px_6px_0px_0px_var(--color-neon-green)] relative overflow-hidden">
            <div className="absolute -right-4 -bottom-4 opacity-20 transform group-hover:scale-125 group-hover:rotate-12 transition-all duration-300">
              <BarChart2 size={140} color="var(--color-neon-green)" />
            </div>
            <div className="relative z-10 flex justify-between items-start">
              <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-green)] bg-black px-4 py-1 rounded-full border-2 border-[var(--color-neon-green)]">AGENT 3</h2>
              <div className="bg-[var(--color-neon-green)] p-2 rounded-xl border-2 border-black group-hover:scale-110 transition-transform">
                <ArrowRight size={20} className="text-black" strokeWidth={3} />
              </div>
            </div>
            <div className="relative z-10">
              <p className="text-white font-bold mb-2 text-sm">Analytics Core</p>
              <div className="flex items-center gap-3 bg-black/50 w-fit px-3 py-2 rounded-xl border-2 border-[var(--color-neon-green)]">
                <div className={`w-3 h-3 rounded-full bg-[var(--color-neon-green)] ${statuses.agent3 === "working" ? "animate-ping" : "animate-pulse"}`} />
                <p className="text-[14px] font-bold text-[var(--color-neon-green)] uppercase font-[var(--font-space)]">{agent3Label.substring(0, 24)}</p>
              </div>
            </div>
          </Link>

          {/* Agent 4 - Yellow */}
          <Link to="/pipeline" className="group bg-[var(--color-panel-bg)] border-4 border-black p-6 rounded-3xl hover:-translate-y-2 hover:shadow-[8px_8px_0px_0px_var(--color-neon-yellow)] transition-all duration-300 ease-out flex flex-col justify-between h-48 shadow-[6px_6px_0px_0px_var(--color-neon-yellow)] relative overflow-hidden">
            <div className="absolute -right-4 -bottom-4 opacity-20 transform group-hover:scale-125 group-hover:rotate-12 transition-all duration-300">
              <Zap size={140} color="var(--color-neon-yellow)" />
            </div>
            <div className="relative z-10 flex justify-between items-start">
              <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-yellow)] bg-black px-4 py-1 rounded-full border-2 border-[var(--color-neon-yellow)]">AGENT 4</h2>
              <div className="bg-[var(--color-neon-yellow)] p-2 rounded-xl border-2 border-black group-hover:scale-110 transition-transform">
                <ArrowRight size={20} className="text-black" strokeWidth={3} />
              </div>
            </div>
            <div className="relative z-10">
              <p className="text-white font-bold mb-2 text-sm">Pipeline Management</p>
              <div className="flex items-center gap-3 bg-black/50 w-fit px-3 py-2 rounded-xl border-2 border-[var(--color-neon-yellow)]">
                <div className={`w-3 h-3 rounded-full bg-[var(--color-neon-yellow)] ${statuses.agent4 === "working" ? "animate-ping" : "animate-pulse"}`} />
                <p className="text-[14px] font-bold text-[var(--color-neon-yellow)] uppercase font-[var(--font-space)]">{agent4Label.substring(0, 24)}</p>
              </div>
            </div>
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
