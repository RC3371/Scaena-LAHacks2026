import React from "react";
import { Link, Outlet, useLocation } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { 
  BarChart2, Home, Send, Compass, Settings, Zap,
  Menu, X, User, Bell, ChevronDown
} from "lucide-react";

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const location = useLocation();

  const navItems = [
    { name: "DASHBOARD", href: "/", icon: Home, color: "var(--color-neon-purple)" },
    { name: "MARKET SCAN", href: "/insights", icon: Compass, color: "var(--color-neon-pink)" },
    { name: "OUTREACH", href: "/outreach", icon: Send, color: "var(--color-neon-cyan)" },
    { name: "ANALYTICS", href: "/analytics", icon: BarChart2, color: "var(--color-neon-green)" },
    { name: "PIPELINE", href: "/pipeline", icon: Zap, color: "var(--color-neon-yellow)" },
  ];

  const activeColor = navItems.find(n => n.href === location.pathname)?.color || "white";

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-dark-bg)] bg-[radial-gradient(rgba(255,255,255,0.05)_2px,transparent_2px)] bg-[length:30px_30px] font-sans text-white">
      
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-40 bg-black/80 lg:hidden" 
            onClick={() => setSidebarOpen(false)} 
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <div 
        className={`fixed lg:static inset-y-0 left-0 z-50 flex-shrink-0 transition-all duration-300 ease-[cubic-bezier(0.4,0,0.2,1)]
          ${sidebarOpen ? "w-[17rem] translate-x-0" : "w-[17rem] lg:w-0 -translate-x-full lg:-translate-x-0 lg:opacity-0 pointer-events-none"}
        `}
      >
        <div 
          className="w-60 m-4 h-[calc(100%-2rem)] bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl flex flex-col overflow-hidden"
          style={{ boxShadow: `6px 6px 0px 0px ${activeColor}` }}
        >
          <div className="p-6 border-b-4 border-black flex flex-col items-center justify-center bg-zinc-900 rounded-t-xl shrink-0 relative overflow-hidden group">
            {/* Animated Y2K Logo */}
            <div className="relative flex items-center justify-center mb-3">
              {/* Star Burst Background */}
              <svg viewBox="0 0 100 100" className="absolute w-24 h-24 opacity-20 group-hover:opacity-40 transition-opacity animate-[spin_15s_linear_infinite]" style={{ color: activeColor }} fill="currentColor">
                <path d="M50 0 L56 38 L95 15 L62 50 L95 85 L56 62 L50 100 L44 62 L5 85 L38 50 L5 15 L44 38 Z" />
              </svg>
              
              {/* Wireframe Globe + Crosshair */}
              <svg viewBox="0 0 100 100" className="w-16 h-16 z-10 drop-shadow-[3px_3px_0px_black] group-hover:scale-110 transition-transform duration-300" style={{ color: activeColor }} fill="none" stroke="currentColor" strokeWidth="5">
                <circle cx="50" cy="50" r="45" />
                <ellipse cx="50" cy="50" rx="18" ry="45" />
                <ellipse cx="50" cy="50" rx="45" ry="18" />
                <line x1="5" y1="50" x2="95" y2="50" />
                <line x1="50" y1="5" x2="50" y2="95" />
              </svg>
              
              {/* Center Pill / Target */}
              <div className="absolute inset-0 flex items-center justify-center z-20">
                <div className="w-4 h-4 bg-white border-4 border-black rounded-full animate-pulse" />
              </div>
            </div>
            
            <h1 className="text-2xl font-[var(--font-bungee)] text-white tracking-widest relative z-10 drop-shadow-[2px_2px_0px_black]">SCAENA OS</h1>
            
            <button 
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden absolute top-3 right-3 p-1 bg-black text-white border-2 border-white rounded-md hover:scale-110 transition-transform z-20 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
            >
              <X size={18} strokeWidth={3} />
            </button>
          </div>

          <nav className="space-y-3 px-3 py-6 flex-1 overflow-y-auto bg-[var(--color-panel-bg)] font-[var(--font-space)]">
            {navItems.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all border-4 ${
                    isActive 
                      ? "text-black font-bold shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]" 
                      : "border-transparent text-zinc-400 hover:border-zinc-700 hover:bg-zinc-800 hover:text-white"
                  }`}
                  style={{ 
                    backgroundColor: isActive ? item.color : undefined,
                    borderColor: isActive ? item.color : undefined
                  }}
                  onClick={() => {
                    if (window.innerWidth < 1024) setSidebarOpen(false);
                  }}
                >
                  <item.icon 
                    size={20} 
                    strokeWidth={isActive ? 3 : 2}
                    className={isActive ? "text-black" : ""} 
                  />
                  <span className="tracking-wider font-bold text-[15px]">
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </nav>
          
          <div className="p-4 border-t-4 border-black bg-zinc-900 rounded-b-xl shrink-0 font-[var(--font-space)]">
            <div className="text-xs text-zinc-400 font-bold mb-2">SYSTEM STATUS:</div>
            <div className="flex items-center space-x-2 bg-black p-2 rounded-full border-2 border-[var(--color-neon-green)]">
              <div className="w-3 h-3 rounded-full bg-[var(--color-neon-green)] animate-ping ml-1" />
              <span className="text-[var(--color-neon-green)] font-bold text-sm tracking-widest">MAXIMUM</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className={`flex-1 flex flex-col min-w-0 relative z-10 py-4 pr-6 transition-all duration-300 ${sidebarOpen ? 'pl-2' : 'pl-6'}`}>
        {/* Topbar */}
        <header 
          className="h-16 flex items-center justify-between px-6 bg-[var(--color-panel-bg)] border-4 border-black rounded-2xl shrink-0 mb-4"
          style={{ boxShadow: `6px 6px 0px 0px ${activeColor}` }}
        >
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 bg-white text-black border-2 border-black rounded-lg hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all"
            >
              <Menu size={20} strokeWidth={3} />
            </button>
            <div className="hidden lg:flex items-center gap-3 text-[14px] font-bold font-[var(--font-space)]">
              <span className="text-white tracking-widest">USER: JORDAN ALEX</span>
              <span className="text-zinc-500">///</span>
              <span className="font-[var(--font-bungee)] tracking-wide" style={{ color: activeColor }}>
                {navItems.find(n => n.href === location.pathname)?.name || "DASHBOARD"}
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <button className="relative text-zinc-400 hover:text-white transition-colors duration-150 hover:scale-110">
              <Bell size={24} strokeWidth={2.5} />
              <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-[var(--color-neon-pink)] border-2 border-black animate-pulse" />
            </button>
            <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center border-4 border-black cursor-pointer hover:shadow-[4px_4px_0px_0px_rgba(255,255,255,1)] transition-all overflow-hidden">
              <User size={20} strokeWidth={3} className="text-black" />
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.15 }}
              className="h-full"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}