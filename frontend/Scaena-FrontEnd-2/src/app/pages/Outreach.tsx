import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Send, MessageSquare, CheckCircle2 } from "lucide-react";

function Typewriter({ text, onComplete }: { text: string, onComplete?: () => void }) {
  const [displayed, setDisplayed] = useState("");
  
  useEffect(() => {
    setDisplayed("");
    let i = 0;
    const timer = setInterval(() => {
      setDisplayed(text.substring(0, i));
      i++;
      if (i > text.length) {
        clearInterval(timer);
        if (onComplete) onComplete();
      }
    }, 10); 
    return () => clearInterval(timer);
  }, [text]);

  return <span>{displayed}</span>;
}

export function Outreach() {
  const [autoPilot, setAutoPilot] = useState(false);
  const [activeId, setActiveId] = useState(1);
  const [isDrafting, setIsDrafting] = useState(false);
  const [isFinalized, setIsFinalized] = useState(false);
  const [strategyInput, setStrategyInput] = useState("");

  const targets = [
    {
      id: 1,
      name: "Tech Retreat",
      contact: "Sarah Jenkins",
      history: [
        { role: "Agent", text: "Reached out regarding Q3 corporate entertainment slot." },
        { role: "Sarah", text: "We typically need 60 minutes of modular interactive material. Do you have that?" }
      ],
      initialDraft: "Hi Sarah,\n\nYes, absolutely. Our live set is highly modular. We regularly adapt our 60-minute headline block into interactive segments perfectly suited for corporate retreats.\n\nI've attached a reel showcasing this exact format from a recent tech summit in Austin.\n\nLet me know if you have time for a brief call next week to discuss logistics.\n\nBest,\nJordan Alex"
    },
    {
      id: 2,
      name: "The Roxy",
      contact: "Mike Rossi",
      history: [
        { role: "Agent", text: "Pitched for local support slot." },
        { role: "Mike", text: "Send over recent local draw metrics." }
      ],
      initialDraft: "Hi Mike,\n\nOur recent residency at The Echo sold out all 4 nights (250 cap). Our Spotify streaming is heavily indexed in LA, with 45k monthly listeners locally.\n\nHappy to send over the complete demographic breakdown.\n\nBest,\nJordan Alex"
    }
  ];

  const activeTarget = targets.find(t => t.id === activeId) || targets[0];
  const [currentDraft, setCurrentDraft] = useState(activeTarget.initialDraft);

  useEffect(() => {
    setCurrentDraft(activeTarget.initialDraft);
    setIsFinalized(false);
    setIsDrafting(true);
  }, [activeId]);

  const handleAdjustPitch = () => {
    if (!strategyInput.trim()) return;
    setIsDrafting(true);
    setIsFinalized(false);
    setCurrentDraft(`[Adjusted based on: "${strategyInput}"]\n\n` + activeTarget.initialDraft.replace("Hi ", "Hello "));
    setStrategyInput("");
  };

  const handleFinalize = () => setIsFinalized(true);

  return (
    <div className="flex flex-col h-full overflow-hidden pr-2 pb-2">
      {/* Top Header */}
      <div className="bg-[var(--color-panel-bg)] border-4 border-black p-5 rounded-2xl shadow-[6px_6px_0px_0px_var(--color-neon-cyan)] flex justify-between items-center shrink-0 mb-6">
        <h1 className="text-xl font-[var(--font-bungee)] text-white bg-black px-6 py-2 rounded-full border-4 border-[var(--color-neon-cyan)] uppercase tracking-wider">AGENT 2 :: OUTREACH</h1>
        <div className="flex items-center bg-black p-2 rounded-xl border-4 border-black gap-2 font-[var(--font-space)]">
          <button 
            onClick={() => setAutoPilot(false)}
            className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all border-2 ${!autoPilot ? 'bg-[var(--color-neon-cyan)] text-black border-[var(--color-neon-cyan)] shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]' : 'border-transparent text-[var(--color-neon-cyan)] hover:bg-[var(--color-panel-bg)]'}`}
          >
            MANUAL APPROVAL
          </button>
          <button 
            onClick={() => setAutoPilot(true)}
            className={`px-4 py-2 rounded-lg text-[13px] font-bold transition-all border-2 ${autoPilot ? 'bg-white text-black border-white shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]' : 'border-transparent text-white hover:bg-[var(--color-panel-bg)]'}`}
          >
            AUTO PITCH [ACTIVE]
          </button>
        </div>
      </div>
      
      {/* Main Split View */}
      <div className="flex flex-1 overflow-hidden gap-6 pr-2 pb-2">
        {/* Left: Targets List */}
        <div className="w-1/3 border-4 border-black bg-[var(--color-panel-bg)] rounded-2xl p-5 overflow-y-auto shadow-[6px_6px_0px_0px_var(--color-neon-cyan)]">
          <h2 className="text-[14px] font-[var(--font-bungee)] text-[var(--color-neon-cyan)] mb-6 bg-black px-4 py-2 rounded-full border-2 border-[var(--color-neon-cyan)] inline-block">TARGETS QUEUED</h2>
          <div className="space-y-4 font-sans">
            {targets.map(target => (
              <button
                key={target.id}
                onClick={() => setActiveId(target.id)}
                className={`w-full text-left px-5 py-4 rounded-xl border-4 transition-all duration-150 ease-out flex flex-col justify-between ${
                  activeId === target.id ? 'bg-[var(--color-neon-cyan)] text-black border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] -translate-y-1' : 'bg-black text-[var(--color-neon-cyan)] border-black hover:border-[var(--color-neon-cyan)]'
                }`}
              >
                <div className="flex justify-between items-start w-full">
                  <p className={`text-lg font-bold ${activeId === target.id ? 'text-black' : 'text-white'}`}>{target.name}</p>
                  <MessageSquare size={20} className={activeId === target.id ? 'text-black' : 'text-[var(--color-neon-cyan)]'} />
                </div>
                <p className={`text-[13px] font-medium mt-2 px-2 py-1 rounded w-fit ${activeId === target.id ? 'bg-black text-[var(--color-neon-cyan)]' : 'bg-[var(--color-panel-bg)] text-[var(--color-neon-cyan)] border border-[var(--color-neon-cyan)]/30'}`}>{target.contact}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Right: Workspace */}
        <div className="w-2/3 flex flex-col gap-6 min-h-0">
          {/* Chat History */}
          <div className="p-6 border-4 border-black bg-black rounded-2xl shadow-[6px_6px_0px_0px_var(--color-neon-cyan)] flex-shrink-0 h-1/3 min-h-[150px] overflow-y-auto font-sans">
            <h2 className="text-[14px] font-[var(--font-bungee)] text-[var(--color-neon-cyan)] mb-4 inline-block border-b-2 border-[var(--color-neon-cyan)] pb-1">COMMS LOG</h2>
            <div className="space-y-4 mt-2">
              {activeTarget.history.map((msg, i) => (
                <div key={i} className={`flex flex-col ${msg.role === 'Agent' ? 'items-end' : 'items-start'}`}>
                  <span className="text-[10px] font-bold text-white bg-[var(--color-panel-bg)] px-2 py-0.5 rounded border border-black uppercase mb-1 font-[var(--font-space)]">{msg.role}</span>
                  <div className={`px-4 py-3 rounded-2xl border-4 border-black max-w-[80%] text-[14px] leading-relaxed font-medium ${
                    msg.role === 'Agent' ? 'bg-[var(--color-neon-cyan)] text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-tr-none' : 'bg-white text-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-tl-none'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pitch Generation & Finalization */}
          <div className="flex-1 border-4 border-black bg-[var(--color-panel-bg)] rounded-2xl shadow-[6px_6px_0px_0px_var(--color-neon-cyan)] flex flex-col overflow-hidden font-sans min-h-0">
            <div className="p-4 border-b-4 border-black bg-[var(--color-neon-cyan)] flex justify-between items-center font-[var(--font-space)]">
              <h2 className="text-[14px] font-[var(--font-bungee)] text-black">GENERATED DRAFT</h2>
              {isDrafting ? (
                <span className="text-[12px] font-bold text-black flex items-center gap-2 bg-white px-2 py-1 rounded-full border-2 border-black">
                  <div className="w-2 h-2 rounded-full bg-black animate-pulse" /> DRAFTING
                </span>
              ) : (
                <span className="text-[12px] font-bold text-white flex items-center gap-2 bg-black px-2 py-1 rounded-full border-2 border-black">
                   <div className="w-2 h-2 rounded-full bg-[var(--color-neon-cyan)]" /> READY
                </span>
              )}
            </div>
            
            <div className="flex-1 p-6 overflow-y-auto">
              <div className="text-[15px] text-zinc-100 bg-black p-6 rounded-xl border-2 border-[var(--color-neon-cyan)] leading-[1.8] whitespace-pre-wrap">
                <Typewriter key={currentDraft} text={currentDraft} onComplete={() => setIsDrafting(false)} />
              </div>

              {/* Final Confirmation State */}
              <AnimatePresence>
                {isFinalized && (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 10 }}
                    className="mt-6 bg-[var(--color-neon-cyan)] border-4 border-black text-black p-5 rounded-2xl flex items-center justify-between shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
                  >
                    <div className="flex items-center gap-4">
                      <CheckCircle2 size={32} className="text-black bg-white rounded-full" />
                      <div>
                        <p className="text-lg font-[var(--font-bungee)]">STRATEGY LOCKED</p>
                        <p className="text-[14px] font-bold mt-1 font-[var(--font-space)] uppercase">Agent 2 initializing dispatch sequence.</p>
                      </div>
                    </div>
                    <button onClick={() => setIsFinalized(false)} className="text-[13px] font-bold bg-black text-white px-4 py-2 rounded-lg hover:bg-white hover:text-black transition-colors border-2 border-black font-[var(--font-space)] uppercase">UNDO</button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            
            {!isFinalized && (
              <div className="p-5 border-t-4 border-black bg-black flex flex-col gap-4">
                <div className="flex gap-3 font-[var(--font-space)]">
                  <input 
                    type="text" 
                    value={strategyInput}
                    onChange={(e) => setStrategyInput(e.target.value)}
                    placeholder="Enter pitch adjustment instructions..." 
                    className="flex-1 bg-[var(--color-panel-bg)] border-2 border-[var(--color-neon-cyan)] rounded-xl px-4 py-3 text-[14px] font-bold text-white placeholder-[var(--color-neon-cyan)]/50 focus:outline-none focus:border-white transition-colors font-sans"
                    onKeyDown={(e) => e.key === 'Enter' && handleAdjustPitch()}
                  />
                  <button 
                    onClick={handleAdjustPitch}
                    className="px-6 py-3 bg-[var(--color-neon-cyan)] border-4 border-black text-black text-[14px] font-bold rounded-full hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all uppercase"
                  >
                    REGENERATE
                  </button>
                </div>
                <div className="flex justify-end gap-4 mt-2 font-[var(--font-space)]">
                  <button 
                    disabled={isDrafting}
                    className="px-6 py-3 bg-[var(--color-panel-bg)] border-2 border-white text-white text-[14px] font-bold rounded-xl hover:bg-white hover:text-black transition-all disabled:opacity-50 uppercase"
                  >
                    DISCARD
                  </button>
                  <button 
                    disabled={isDrafting}
                    onClick={handleFinalize}
                    className="px-8 py-3 bg-[var(--color-neon-cyan)] text-black border-4 border-black text-[14px] font-[var(--font-bungee)] rounded-xl hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] transition-all flex items-center gap-3 disabled:opacity-50 disabled:pointer-events-none"
                  >
                    <Send size={18} strokeWidth={3} />
                    APPROVE PITCH
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}