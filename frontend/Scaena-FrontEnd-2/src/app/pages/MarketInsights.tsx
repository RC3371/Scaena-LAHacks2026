import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Search, Terminal } from "lucide-react";

export function MarketInsights() {
  const [isScanning, setIsScanning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [displayedVenues, setDisplayedVenues] = useState<any[]>([]);

  const allVenues = [
    { name: "THE ROXY", type: "Club", location: "Los Angeles", score: 98 },
    { name: "TECH RETREAT", type: "Corporate Retreat", location: "San Francisco", score: 88 },
    { name: "SXSW SHOWCASE", type: "Festival", location: "Austin", score: 62 },
    { name: "COACHELLA TENT", type: "Festival", location: "Indio", score: 45 },
  ];

  const handleScan = () => {
    setIsScanning(true);
    setLogs([]);
    setDisplayedVenues([]);
    
    const scanSteps = [
      "> INITIATING SCAN :: DIRECTIVE UPDATED",
      "> CRAWLING CORPORATE SCHEDULES // Q3-Q4",
      "> ANALYZING BOOKING PATTERNS :: THE ROXY",
      "> CROSS REF :: SPOTIFY DENSITY (SF, LA)",
      "> FILTERING MISMATCH :: CAP < 200",
      "> SCAN COMPLETE :: SCORES CALCULATED"
    ];

    let step = 0;
    const interval = setInterval(() => {
      if (step < scanSteps.length) {
        setLogs(prev => [...prev, scanSteps[step]]);
        step++;
      } else {
        clearInterval(interval);
        setIsScanning(false);
        setDisplayedVenues(allVenues);
      }
    }, 600);
  };

  useEffect(() => {
    handleScan();
  }, []);

  return (
    <div className="flex flex-col h-full overflow-hidden pr-2 pb-2">
      {/* Top Header Controls */}
      <div className="bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-5 flex flex-col gap-4 shadow-[6px_6px_0px_0px_var(--color-neon-pink)] mb-6 shrink-0">
        <div className="flex items-center gap-3 bg-black border-4 border-[var(--color-neon-pink)] w-fit px-6 py-2 rounded-full">
          <div className={`w-3 h-3 rounded-full ${isScanning ? 'bg-[var(--color-neon-pink)] animate-ping' : 'bg-[var(--color-neon-pink)]'}`} />
          <h1 className="text-xl font-[var(--font-bungee)] text-white tracking-wider uppercase">
            {isScanning ? "AGENT 1 :: SCANNING..." : "AGENT 1 :: STANDBY"}
          </h1>
        </div>
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-[var(--color-neon-pink)]" size={20} strokeWidth={3} />
            <input 
              type="text" 
              placeholder="Enter override parameters (e.g. focus on tech retreats...)" 
              className="w-full bg-black border-4 border-black rounded-full pl-12 pr-4 py-3 text-[15px] text-white placeholder-[var(--color-neon-pink)]/50 focus:outline-none focus:border-[var(--color-neon-pink)] focus:shadow-[0_0_15px_var(--color-neon-pink)] transition-all font-sans" 
              onKeyDown={(e) => e.key === 'Enter' && handleScan()}
            />
          </div>
          <button 
            onClick={handleScan}
            disabled={isScanning}
            className="px-6 py-3 bg-[var(--color-neon-pink)] text-black border-4 border-black text-[14px] font-bold rounded-full hover:bg-white hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all uppercase whitespace-nowrap disabled:opacity-50 disabled:pointer-events-none font-[var(--font-space)]"
          >
            UPDATE DIRECTIVE
          </button>
        </div>
      </div>
      
      {/* Main Split View */}
      <div className="flex flex-1 overflow-hidden gap-6 pr-2 pb-2">
        {/* Left: Agent Working Visualizer */}
        <div className="w-1/3 border-4 border-black bg-black rounded-2xl p-5 flex flex-col shadow-[6px_6px_0px_0px_var(--color-neon-pink)]">
          <div className="flex items-center gap-3 mb-6 bg-[var(--color-panel-bg)] p-2 rounded-xl border-2 border-[var(--color-neon-pink)] w-fit">
            <Terminal size={20} className="text-[var(--color-neon-pink)]" strokeWidth={3} />
            <h2 className="text-[14px] font-[var(--font-bungee)] text-[var(--color-neon-pink)]">SYS LOG</h2>
          </div>
          <div className="flex-1 overflow-auto space-y-3 pr-2 font-[var(--font-space)]">
            <AnimatePresence>
              {logs.map((log, i) => (
                <motion.div 
                  key={i}
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-[13px] text-[var(--color-neon-pink)] uppercase font-bold leading-relaxed bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-pink)] p-3 rounded-lg"
                  style={{ textShadow: '0 0 5px var(--color-neon-pink)' }}
                >
                  {log}
                </motion.div>
              ))}
            </AnimatePresence>
            {isScanning && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-[var(--color-neon-pink)] text-[16px] font-bold mt-4 bg-black border-2 border-[var(--color-neon-pink)] p-2 rounded w-fit"
              >
                <span className="animate-pulse">_</span>PROCESSING
              </motion.div>
            )}
          </div>
        </div>

        {/* Right: Data Feed */}
        <div className="w-2/3 overflow-auto bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl p-6 shadow-[6px_6px_0px_0px_var(--color-neon-pink)]">
          <h2 className="text-xl font-[var(--font-bungee)] text-[var(--color-neon-pink)] mb-6 bg-black inline-block px-4 py-2 border-2 border-[var(--color-neon-pink)] rounded-full">MATCH FEED</h2>
          
          <div className="grid grid-cols-1 gap-4">
            <AnimatePresence>
              {displayedVenues.map((venue, i) => {
                let color = "text-[var(--color-neon-pink)]"; 
                let barColor = "bg-[var(--color-neon-pink)]";

                return (
                  <motion.div 
                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ duration: 0.2, delay: i * 0.05 }}
                    key={venue.name} 
                    className="bg-black border-4 border-black p-5 rounded-2xl flex items-center justify-between hover:border-[var(--color-neon-pink)] hover:shadow-[4px_4px_0px_0px_var(--color-neon-pink)] transition-all"
                  >
                    <div>
                      <h3 className="text-xl font-[var(--font-bungee)] text-white tracking-widest">{venue.name}</h3>
                      <p className="text-[14px] text-zinc-300 mt-2 bg-[var(--color-panel-bg)] inline-block px-3 py-1.5 rounded-lg border border-[var(--color-neon-pink)]/30 font-sans">
                        <span className="font-semibold text-white">{venue.type}</span> 
                        <span className="mx-2 text-[var(--color-neon-pink)]">—</span> 
                        {venue.location}
                      </p>
                    </div>
                    
                    <div className="flex flex-col items-end gap-3 w-40 font-[var(--font-space)]">
                      <div className="flex justify-between w-full items-baseline bg-[var(--color-panel-bg)] px-3 py-1 rounded-full border-2 border-black">
                        <span className="text-[12px] font-bold text-white">MATCH</span>
                        <span className={`text-xl font-[var(--font-bungee)] ${color}`} style={{ textShadow: `2px 2px 0 var(--color-panel-bg)` }}>{venue.score}%</span>
                      </div>
                      <div className="w-full h-3 rounded-full bg-[var(--color-panel-bg)] border-2 border-black overflow-hidden relative">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${venue.score}%` }}
                          transition={{ duration: 0.6, delay: i * 0.1 + 0.2 }}
                          className={`absolute top-0 bottom-0 left-0 ${barColor}`} 
                          style={{ opacity: venue.score < 50 ? 0.3 : venue.score < 80 ? 0.6 : 1 }}
                        />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
            {!isScanning && displayedVenues.length === 0 && (
              <div className="text-[16px] font-bold font-[var(--font-space)] text-[var(--color-neon-pink)] mt-10 text-center uppercase bg-black p-4 rounded-xl border-2 border-dashed border-[var(--color-neon-pink)]">
                AWAITING NEW DIRECTIVE
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}