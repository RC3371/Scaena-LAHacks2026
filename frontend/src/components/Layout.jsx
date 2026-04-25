import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Search, Users, Mail, BarChart3, Bell, LogOut, Zap } from 'lucide-react'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/research', icon: Search, label: 'Market Research' },
  { to: '/prospects', icon: Users, label: 'Prospects' },
  { to: '/pitches', icon: Mail, label: 'Pitches' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/followups', icon: Bell, label: 'Follow-Ups' },
]

export default function Layout() {
  const navigate = useNavigate()

  function handleLogout() {
    localStorage.removeItem('profileId')
    navigate('/setup')
  }

  return (
    <div className="flex h-screen bg-gray-950">
      <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white text-sm">GigAI</h1>
              <p className="text-gray-500 text-xs">Booking Automation</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-800 w-full transition-colors"
          >
            <LogOut size={16} />
            Switch Profile
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
