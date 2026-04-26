function Sidebar() {
  const menuItems = [
    { icon: 'sparkles', label: 'DASHBOARD', active: true },
    { icon: 'disc', label: 'HYPE BOTS' },
    { icon: 'radio', label: 'CAMPAIGNS' },
    { icon: 'book-open', label: 'VENUE ROLODEX' },
    { icon: 'sliders', label: 'STUDIO CONFIG' },
  ];

  return (
    <div className="w-64 flex-shrink-0 y2k-panel m-4 flex flex-col bg-[var(--neon-pink)] border-4 border-black" data-name="sidebar" data-file="components/Sidebar.js">
      <div className="p-4 border-b-4 border-black flex items-center justify-center space-x-2 bg-[var(--neon-yellow)] rounded-t-xl">
        <div className="icon-headphones text-3xl text-black animate-bounce"></div>
        <h1 className="text-3xl pixel-text text-black mt-1">STAR_SYNC</h1>
      </div>
      
      <div className="flex-1 overflow-y-auto py-4 bg-[var(--panel-bg)]">
        <nav className="space-y-2 px-2">
          {menuItems.map((item, index) => (
            <a
              key={index}
              href="#"
              className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all border-4 border-transparent ${
                item.active 
                  ? 'bg-[var(--neon-pink)] text-black border-black font-bold shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]' 
                  : 'text-[var(--neon-cyan)] hover:border-black hover:bg-[var(--neon-cyan)] hover:text-black hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]'
              }`}
            >
              <div className={`icon-${item.icon} text-xl`}></div>
              <span className="tracking-wider font-bold">{item.label}</span>
            </a>
          ))}
        </nav>
      </div>

      <div className="p-4 border-t-4 border-black bg-[var(--neon-purple)] rounded-b-xl">
        <div className="text-xs text-[var(--neon-cyan)] font-bold mb-2">VIBE CHECK:</div>
        <div className="flex items-center space-x-2 bg-black p-2 rounded-full border-2 border-[var(--neon-green)]">
          <div className="w-3 h-3 rounded-full bg-[var(--neon-green)] animate-ping ml-1"></div>
          <span className="text-[var(--neon-green)] font-bold text-sm">MAXIMUM</span>
        </div>
      </div>
    </div>
  );
}