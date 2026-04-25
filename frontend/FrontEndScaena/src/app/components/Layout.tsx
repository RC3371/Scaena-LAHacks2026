import React from "react";
import { Link, Outlet, useLocation } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import { 
  BarChart3, Home, Mail, Search, Settings, Zap,
  Menu, X, User, Bell, Drama
} from "lucide-react";

export function Layout() {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const location = useLocation();

  const navItems = [
    { name: "Overview", href: "/", icon: Home },
    { name: "Insights", href: "/insights", icon: Search },
    { name: "Outreach", href: "/outreach", icon: Mail },
    { name: "Analytics", href: "/analytics", icon: BarChart3 },
    { name: "Pipeline", href: "/pipeline", icon: Zap },
  ];

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden font-sans antialiased selection:bg-[#37afef]/30 selection:text-slate-900">
      
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden" 
            onClick={() => setSidebarOpen(false)} 
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <div 
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-slate-200 transform transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] lg:static lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between h-20 px-8 border-b border-slate-100 relative">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#37afef] rounded-md flex items-center justify-center shadow-sm">
              <Drama size={22} className="text-white" strokeWidth={2} />
            </div>
            <span className="text-xl font-extrabold tracking-tight text-slate-900 uppercase">Scaena</span>
          </div>
          <button 
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden p-2 text-slate-400 hover:text-slate-900 transition-colors"
          >
            <X size={20} strokeWidth={2} />
          </button>
        </div>

        <nav className="px-4 py-8 space-y-1 overflow-y-auto h-[calc(100vh-160px)]">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-6 px-4">
            Production Deck
          </div>
          {navItems.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`relative flex items-center gap-3 px-4 py-3 rounded-md group transition-all duration-200 ${
                  isActive 
                    ? "bg-[#37afef]/10 text-[#37afef]" 
                    : "bg-transparent text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon 
                  size={18} 
                  strokeWidth={isActive ? 2.5 : 2}
                  className={`relative z-10 transition-colors duration-200 ${isActive ? "text-[#37afef]" : "text-slate-400 group-hover:text-[#37afef]"}`} 
                />
                <span className={`relative z-10 text-sm font-semibold tracking-wide transition-colors duration-200`}>
                  {item.name}
                </span>
                {isActive && (
                  <motion.div 
                    layoutId="activeNavAccent"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-[#37afef] rounded-r-md"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}
        </nav>
        
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-200 bg-white">
          <button className="flex items-center gap-3 w-full px-4 py-3 rounded-md text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-all duration-200 group">
            <Settings size={18} strokeWidth={2} className="text-slate-400 group-hover:text-slate-900 group-hover:rotate-90 transition-all duration-500" />
            <span className="text-sm font-semibold tracking-wide">Settings</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 relative z-10">
        {/* Topbar */}
        <header className="h-20 flex items-center justify-between px-8 bg-white/80 backdrop-blur-md border-b border-slate-200 relative">
          <button 
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 -ml-2 text-slate-500 hover:text-slate-900 transition-colors"
          >
            <Menu size={20} strokeWidth={2} />
          </button>
          
          <div className="hidden lg:block lg:flex-1" />
          
          <div className="flex items-center gap-6">
            <button className="relative text-slate-400 hover:text-slate-900 transition-colors duration-200">
              <Bell size={20} strokeWidth={2} />
              <span className="absolute 0 right-0 w-2.5 h-2.5 rounded-full bg-[#37afef] border-2 border-white" />
            </button>
            <div className="h-6 w-px bg-slate-200" />
            <div className="flex items-center gap-3 cursor-pointer group">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-bold text-slate-900 tracking-tight">Alex Maker</p>
                <p className="text-[10px] text-slate-500 tracking-widest uppercase font-semibold">Director</p>
              </div>
              <div className="w-9 h-9 rounded-md bg-slate-100 flex items-center justify-center border border-slate-200 group-hover:border-[#37afef] transition-colors duration-200">
                <User size={16} strokeWidth={2} className="text-slate-500 group-hover:text-[#37afef] transition-colors" />
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto relative p-6 sm:p-10 lg:p-12">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="h-full max-w-7xl mx-auto"
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}