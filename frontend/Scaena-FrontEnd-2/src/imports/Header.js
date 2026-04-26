function Header() {
  return (
    <header className="h-16 mt-4 mr-4 y2k-panel-cyan flex items-center justify-between px-6 bg-[var(--neon-cyan)]" data-name="header" data-file="components/Header.js">
      <div className="flex items-center overflow-hidden whitespace-nowrap w-2/3 border-r-4 border-black pr-4">
        <div className="bg-black text-[var(--neon-yellow)] font-bold px-3 py-1 rounded-full border-2 border-[var(--neon-pink)] mr-4 text-sm animate-pulse">HOT GOSSIP:</div>
        <marquee className="text-sm text-black tracking-widest font-bold font-mono">
           ✨ YOUR LATEST TRACK IS TRENDING IN LA ✨ THE COMEDY STORE SHOW SOLD OUT ✨ NEW FAN MAIL DETECTED ✨ VENUE MANAGER REPLIED TO PITCH ✨
        </marquee>
      </div>
      
      <div className="flex items-center space-x-6 text-black">
        <div className="flex items-center space-x-2 cursor-pointer hover:text-[var(--neon-pink)] transition-colors">
          <div className="icon-bell text-2xl"></div>
          <span className="bg-[var(--neon-pink)] text-black border-2 border-black text-xs font-bold px-2 py-0.5 rounded-full shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">3</span>
        </div>
        <div className="flex items-center space-x-3 cursor-pointer bg-white px-3 py-1 rounded-full border-2 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-1 hover:translate-y-1 hover:shadow-none transition-all">
          <div className="w-8 h-8 bg-[var(--neon-yellow)] rounded-full border-2 border-black flex items-center justify-center text-black">
            <div className="icon-star text-sm"></div>
          </div>
          <span className="font-bold text-black uppercase text-sm">VIP_STAR</span>
        </div>
      </div>
    </header>
  );
}
