import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Terminal, Cpu, MessageSquare } from "lucide-react";

export function Analytics() {
  const [thoughts, setThoughts] = useState<string[]>([]);
  
  const allThoughts = [
    "> INGESTING LOGS :: AGENT 2",
    "> ANALYZING :: 14 REJECTIONS (T-30D)",
    "> PATTERN FOUND :: 45MIN SET LENGTH REJECTED BY CORP",
    "> CROSS REF :: AGENT 4 SUCCESS LOGS",
    "> EXTRACTING SENTIMENT :: BUYERS REQUIRE 60MIN MODULAR + LOCAL DRAW",
    "> UPDATING GLOBAL MATRIX :: 100%",
    "> INJECTING PARAMS -> AGENT 1 & AGENT 2",
    "> CYCLE COMPLETE :: AWAITING DATA"
  ];

  useEffect(() => {
    let currentIdx = 0;
    const timer = setInterval(() => {
      if (currentIdx < allThoughts.length) {
        setThoughts(prev => [...prev, allThoughts[currentIdx]]);
        currentIdx++;
      } else {
        clearInterval(timer);
      }
    }, 1800); 
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex flex-col h-full overflow-hidden pr-2 pb-2">
      {/* Top Header */}
      <div className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-5 shadow-[6px_6px_0px_0px_var(--color-neon-green)] flex items-center gap-4 shrink-0 mb-6">
        <h1 className="text-xl font-[var(--font-bungee)] text-white bg-black px-6 py-2 rounded-full border-4 border-[var(--color-neon-green)] uppercase tracking-wider">AGENT 3 :: ANALYTICS CORE</h1>
      </div>
      
      {/* Split View */}
      <div className="flex flex-1 overflow-hidden gap-6 pr-2 pb-2">
        
        {/* Left: Visual Thought Stream */}
        <div className="w-1/3 bg-black border-4 border-black rounded-2xl p-6 flex flex-col relative overflow-hidden shadow-[6px_6px_0px_0px_var(--color-neon-green)]">
          <div className="flex items-center gap-3 mb-6 bg-[var(--color-neon-green)] p-2 rounded-xl border-2 border-black w-fit">
            <Terminal size={20} className="text-black" strokeWidth={3} />
            <h2 className="text-[14px] font-[var(--font-bungee)] text-black">LOGIC STREAM</h2>
          </div>
          
          <div className="flex-1 overflow-auto pr-2 relative z-10 font-[var(--font-space)]">
            <div className="relative pb-8 pt-2 min-h-full">
              <div className={`absolute left-[10px] top-4 ${thoughts.length === allThoughts.length ? 'bottom-[50px]' : 'bottom-14'} w-[4px] bg-[var(--color-neon-green)] z-0`} />
              <div className="space-y-6 relative z-10">
                <AnimatePresence>
                  {thoughts.map((thought, i) => (
                    <motion.div 
                      key={i}
                      initial={{ opacity: 0, y: 10, scale: 0.9 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      className="relative pl-8"
                    >
                      <div className="absolute left-0 top-1.5 w-6 h-6 rounded-full bg-black border-4 border-[var(--color-neon-green)] z-10" />
                      <div className="text-[13px] font-bold text-[var(--color-neon-green)] uppercase leading-relaxed bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-green)] p-3 rounded-xl shadow-[2px_2px_0px_0px_var(--color-neon-green)]">
                        {thought}
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
                {thoughts.length < allThoughts.length && (
                  <div className="relative pl-8 pt-2">
                    <div className="absolute left-0 top-3 w-6 h-6 rounded-full bg-[var(--color-neon-green)] animate-ping z-10" />
                    <div className="absolute left-0 top-3 w-6 h-6 rounded-full bg-black border-4 border-[var(--color-neon-green)] z-10" />
                    <div className="text-[12px] font-bold text-[var(--color-neon-green)] uppercase bg-black border border-dashed border-[var(--color-neon-green)] px-3 py-2 rounded-lg w-fit">PROCESSING NODES...</div>
                  </div>
                )}
              </div>
              {/* Extended line for end of stream */}
              {thoughts.length === allThoughts.length && (
                <div className="h-8 relative pl-8 mt-6">
                  <div className="absolute left-[4px] bottom-[10px] w-4 h-4 rounded-full bg-[var(--color-neon-green)] z-10 border-4 border-black" />
                  <div className="text-[12px] font-bold text-zinc-500 uppercase bg-black border border-dashed border-zinc-600 px-3 py-1 rounded-lg w-fit absolute top-1">STREAM COMPLETE</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Insights */}
        <div className="w-2/3 bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-8 overflow-auto shadow-[6px_6px_0px_0px_var(--color-neon-green)] font-sans">
          <h2 className="text-2xl font-[var(--font-bungee)] text-[var(--color-neon-green)] mb-8 bg-black px-6 py-2 rounded-full border-2 border-[var(--color-neon-green)] inline-block">EXTRACTED INTEL</h2>
          
          <div className="grid grid-cols-1 gap-8">
            {/* What Works */}
            <div className="bg-black border-4 border-black rounded-2xl p-6 shadow-[6px_6px_0px_0px_var(--color-neon-green)]">
              <h3 className="text-[16px] font-[var(--font-bungee)] text-black bg-[var(--color-neon-green)] px-4 py-2 rounded-xl mb-6 inline-flex items-center gap-3 border-2 border-black">
                <div className="w-3 h-3 rounded-full bg-white border border-black animate-pulse" /> POSITIVE SIGNALS
              </h3>
              <ul className="space-y-6">
                <li className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0 border border-black" />
                  <p className="text-[16px] text-zinc-100 leading-relaxed font-medium">Emphasizing modular 60-minute sets increases corporate open rates by <span className="text-[var(--color-neon-green)] text-xl mx-1 font-[var(--font-bungee)]">82%</span>.</p>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0 border border-black" />
                  <p className="text-[16px] text-zinc-100 leading-relaxed font-medium">Including direct local draw metrics in initial outreach correlates with <span className="text-[var(--color-neon-green)] text-xl mx-1 font-[var(--font-bungee)]">65%</span> faster reply time.</p>
                </li>
              </ul>
            </div>

            {/* What Doesn't */}
            <div className="bg-black border-4 border-black rounded-2xl p-6 shadow-[6px_6px_0px_0px_var(--color-neon-green)]">
              <h3 className="text-[16px] font-[var(--font-bungee)] text-black bg-[var(--color-neon-green)] px-4 py-2 rounded-xl mb-6 inline-flex items-center gap-3 border-2 border-black">
                <div className="w-3 h-3 rounded-full bg-white border border-black animate-pulse" /> NEGATIVE FRICTION
              </h3>
              <ul className="space-y-6">
                <li className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0 border border-black" />
                  <p className="text-[16px] text-zinc-100 leading-relaxed font-medium">Pitching standard 45-minute club routines to festival buyers yields only <span className="text-[var(--color-neon-green)] text-xl mx-1 font-[var(--font-bungee)]">12%</span> reply rate.</p>
                </li>
                <li className="flex items-start gap-4">
                  <div className="w-3 h-3 rounded-sm bg-[var(--color-neon-green)] mt-1.5 shrink-0 border border-black" />
                  <p className="text-[16px] text-zinc-100 leading-relaxed font-medium">Emails sent after 3PM local venue time see a <span className="text-[var(--color-neon-green)] text-xl mx-1 font-[var(--font-bungee)]">40%</span> drop in next-day response.</p>
                </li>
              </ul>
            </div>
          </div>
          
          <div className="mt-10 pt-8 border-t-4 border-black flex items-center gap-6">
            <button className="px-6 py-4 bg-[var(--color-neon-green)] text-black border-4 border-black font-[var(--font-bungee)] rounded-xl hover:bg-white hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all flex items-center gap-3 text-[16px]">
              <MessageSquare size={20} strokeWidth={3} />
              UPDATE DIRECTIVES
            </button>
            <span className="text-[13px] font-bold text-[var(--color-neon-green)] bg-black px-4 py-2 rounded-xl border-2 border-dashed border-[var(--color-neon-green)] font-[var(--font-space)] uppercase">AGENT 1 & 2 WILL SYNC THESE RULES.</span>
          </div>
        </div>

      </div>
    </div>
  );
}