import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { RefreshCw, FileText, CheckCircle } from "lucide-react";

export function Pipeline() {
  const [activeRebook, setActiveRebook] = useState<number | null>(null);

  const secured = [
    { 
      target: "The Roxy", 
      logs: [
        { time: "Yesterday, 14:00", actor: "AGENT 4", action: "Deal secured. Requested tech rider specifics." },
        { time: "Yesterday, 16:15", actor: "THE ROXY", action: "Provided audio spec sheet. Requested hospitality rider." },
        { time: "Today, 09:00", actor: "AGENT 4", action: "Sent approved hospitality rider. Awaiting countersignature." }
      ]
    },
  ];

  const rebooking = [
    { id: 1, target: "The Comedy Cellar", note: "Last played 6 months ago. High success metric. Q4 dates opening soon.", status: "idle" }
  ];

  const handleRebook = (id: number) => {
    setActiveRebook(id);
    setTimeout(() => {
      setActiveRebook(null);
    }, 3000);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden pr-2 pb-2">
      {/* Top Header */}
      <div className="bg-[var(--color-panel-bg)] border-4 border-black p-5 rounded-2xl shadow-[6px_6px_0px_0px_var(--color-neon-yellow)] flex justify-between items-center shrink-0 mb-6">
        <h1 className="text-xl font-[var(--font-bungee)] text-white bg-black px-6 py-2 rounded-full border-4 border-[var(--color-neon-yellow)] uppercase tracking-wider">AGENT 4 :: PIPELINE</h1>
      </div>
      
      {/* Scrollable Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 overflow-y-auto pr-2 pb-2">
        
        {/* Left Column: Live Communication & Logistics */}
        <div className="space-y-8 font-sans">
          <section className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-6 shadow-[6px_6px_0px_0px_var(--color-neon-yellow)]">
            <h2 className="text-[16px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] mb-6 flex items-center gap-3 border-b-4 border-black pb-4">
              <FileText size={24} strokeWidth={3} /> SECURED DEALS
            </h2>
            <div className="space-y-6">
              {secured.map((deal, i) => (
                <div key={i} className="bg-black border-4 border-black rounded-2xl overflow-hidden shadow-[4px_4px_0px_0px_var(--color-neon-yellow)]">
                  <div className="bg-[var(--color-neon-yellow)] border-b-4 border-black p-4 flex justify-between items-center">
                    <h3 className="text-[18px] font-[var(--font-bungee)] text-black">{deal.target}</h3>
                    <span className="text-[12px] font-bold text-white bg-black px-3 py-1 rounded-full border-2 border-black font-[var(--font-space)] uppercase">ADVANCING SHOW</span>
                  </div>
                  <div className="p-6 space-y-6">
                    {deal.logs.map((log, idx) => (
                      <div key={idx} className="flex gap-4">
                        <div className="flex flex-col items-center mt-1">
                          <div className={`w-4 h-4 rounded-sm border-2 border-black ${log.actor === 'AGENT 4' ? 'bg-[var(--color-neon-yellow)]' : 'bg-white'}`} />
                          {idx !== deal.logs.length - 1 && <div className="w-[4px] h-full bg-[var(--color-panel-bg)] my-2" />}
                        </div>
                        <div className="bg-[var(--color-panel-bg)] p-4 rounded-xl border-2 border-black flex-1">
                          <p className={`text-[12px] font-[var(--font-bungee)] mb-2 ${log.actor === 'AGENT 4' ? 'text-[var(--color-neon-yellow)]' : 'text-white'}`}>{log.actor} // {log.time}</p>
                          <p className="text-[14px] font-semibold text-white">{log.action}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column: Re-engagement */}
        <div className="space-y-8 font-sans">
          <section className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-6 shadow-[6px_6px_0px_0px_var(--color-neon-yellow)]">
            <h2 className="text-[16px] font-[var(--font-bungee)] text-[var(--color-neon-yellow)] mb-6 flex items-center gap-3 border-b-4 border-black pb-4">
              <RefreshCw size={24} strokeWidth={3} /> REBOOK ENGINE
            </h2>
            <div className="space-y-6">
              {rebooking.map((item) => (
                <div key={item.id} className="bg-black border-4 border-black p-6 rounded-2xl shadow-[4px_4px_0px_0px_var(--color-neon-yellow)]">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-[18px] font-[var(--font-bungee)] text-white">{item.target}</h3>
                    <span className="text-[12px] font-bold bg-[var(--color-neon-yellow)] text-black px-3 py-1 rounded-full border-2 border-black font-[var(--font-space)] uppercase">OPPORTUNITY</span>
                  </div>
                  <p className="text-[15px] font-medium text-zinc-100 mb-6 border-l-4 border-[var(--color-neon-yellow)] pl-4 leading-relaxed">{item.note}</p>
                  
                  <AnimatePresence mode="wait">
                    {activeRebook === item.id ? (
                      <motion.div 
                        key="loading"
                        initial={{ opacity: 0 }} 
                        animate={{ opacity: 1 }} 
                        exit={{ opacity: 0 }}
                        className="w-full py-3 bg-[var(--color-panel-bg)] border-4 border-black text-[var(--color-neon-yellow)] text-[14px] font-bold rounded-xl flex justify-center items-center gap-3 font-[var(--font-space)] uppercase"
                      >
                        <div className="w-5 h-5 border-4 border-[var(--color-neon-yellow)] border-t-transparent rounded-full animate-spin" />
                        INITIATING SEQUENCE...
                      </motion.div>
                    ) : (
                      <motion.button 
                        key="button"
                        initial={{ opacity: 0 }} 
                        animate={{ opacity: 1 }} 
                        exit={{ opacity: 0 }}
                        onClick={() => handleRebook(item.id)}
                        className="w-full py-3 bg-[var(--color-neon-yellow)] text-black border-4 border-black text-[16px] font-[var(--font-bungee)] rounded-xl hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all uppercase"
                      >
                        INITIATE REBOOK
                      </motion.button>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
          </section>
          
          <div className="bg-[var(--color-neon-yellow)] border-4 border-black p-6 rounded-2xl flex items-start gap-4 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
            <CheckCircle size={24} className="text-black shrink-0 mt-0.5" strokeWidth={3} />
            <p className="text-[14px] font-bold text-black uppercase leading-relaxed font-[var(--font-space)]">
              AGENT 4 CONTINUALLY ROUTES CONVERSION METRICS AND BUYER RESPONSES BACK TO AGENT 3 TO REFINE FUTURE PITCHES.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}