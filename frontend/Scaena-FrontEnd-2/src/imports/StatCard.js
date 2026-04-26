function StatCard({ title, value, icon, trend, color }) {
  const colorMap = {
    pink: 'var(--neon-pink)',
    cyan: 'var(--neon-cyan)',
    green: 'var(--neon-green)'
  };
  
  const selectedColor = colorMap[color] || colorMap.cyan;

  return (
    <div 
      className="p-6 relative overflow-hidden group border-4 border-black rounded-3xl"
      style={{ 
        backgroundColor: 'var(--panel-bg)',
        boxShadow: `6px 6px 0px 0px ${selectedColor}` 
      }}
      data-name="stat-card" 
      data-file="components/StatCard.js"
    >
      <div className="absolute -right-4 -bottom-4 opacity-20 transform group-hover:scale-125 group-hover:rotate-12 transition-all duration-300">
        <div className={`icon-${icon}`} style={{ fontSize: '8rem', color: selectedColor }}></div>
      </div>
      
      <div className="relative z-10">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-white bg-black px-3 py-1 rounded-full border-2 text-xs font-bold" style={{ borderColor: selectedColor }}>{title}</h3>
          <div className={`icon-${icon} text-3xl drop-shadow-md`} style={{ color: selectedColor }}></div>
        </div>
        <div className="text-5xl pixel-text text-white mb-2" style={{ textShadow: `2px 2px 0px ${selectedColor}` }}>{value}</div>
        <div className="flex items-center space-x-2 text-sm bg-black/50 w-fit px-2 py-1 rounded-lg">
          <span className="text-[var(--neon-green)] font-bold">{trend}</span>
          <span className="text-gray-300">vs last week</span>
        </div>
      </div>
    </div>
  );
}