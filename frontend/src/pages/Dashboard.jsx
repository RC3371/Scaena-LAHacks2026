import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { profilesApi, analyticsApi, followupsApi } from '../api/client'
import { TrendingUp, Mail, Users, Calendar, ChevronRight, Zap, Bell, BarChart3, Search } from 'lucide-react'

function StatCard({ label, value, sub, icon: Icon, color = 'indigo' }) {
  const colors = {
    indigo: 'bg-indigo-600/10 text-indigo-400',
    green: 'bg-green-600/10 text-green-400',
    amber: 'bg-amber-600/10 text-amber-400',
    blue: 'bg-blue-600/10 text-blue-400',
  }
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-gray-400 text-sm">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${colors[color]}`}>
          <Icon size={16} />
        </div>
      </div>
      <p className="text-2xl font-bold text-white">{value}</p>
      {sub && <p className="text-gray-500 text-xs mt-1">{sub}</p>}
    </div>
  )
}

function AgentCard({ number, name, description, status, to, icon: Icon }) {
  return (
    <Link to={to} className="group bg-gray-900 border border-gray-800 hover:border-indigo-600 rounded-xl p-5 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-indigo-600/10 rounded-lg flex items-center justify-center text-indigo-400">
            <Icon size={18} />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-mono">Agent {number}</p>
            <p className="text-sm font-semibold text-white">{name}</p>
          </div>
        </div>
        <ChevronRight size={16} className="text-gray-600 group-hover:text-indigo-400 transition-colors" />
      </div>
      <p className="text-gray-400 text-xs">{description}</p>
      {status && (
        <div className="mt-3 flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span className="text-green-400 text-xs">{status}</span>
        </div>
      )}
    </Link>
  )
}

export default function Dashboard() {
  const profileId = localStorage.getItem('profileId')
  const [profile, setProfile] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [dueFollowups, setDueFollowups] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [p, a, f] = await Promise.all([
          profilesApi.get(profileId),
          analyticsApi.get(profileId).catch(() => null),
          followupsApi.getDue(profileId).catch(() => []),
        ])
        setProfile(p)
        setAnalytics(a)
        setDueFollowups(f)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [profileId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  const summary = analytics?.summary || {}

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-2xl font-bold text-white">
            Welcome back{profile ? `, ${profile.name}` : ''}
          </h1>
          {profile && (
            <span className="px-2.5 py-0.5 bg-indigo-600/10 border border-indigo-600/30 rounded-full text-indigo-400 text-xs capitalize">
              {profile.entertainer_type}
            </span>
          )}
        </div>
        <p className="text-gray-400">Your AI booking pipeline is active and learning.</p>
      </div>

      {dueFollowups.length > 0 && (
        <div className="mb-6 bg-amber-600/10 border border-amber-600/30 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Bell size={18} className="text-amber-400" />
            <div>
              <p className="text-white text-sm font-medium">
                {dueFollowups.length} follow-up{dueFollowups.length !== 1 ? 's' : ''} ready to send
              </p>
              <p className="text-amber-400/70 text-xs">Venues are waiting — send now to recover bookings</p>
            </div>
          </div>
          <Link
            to="/followups"
            className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-medium rounded-lg transition-colors"
          >
            View Follow-Ups
          </Link>
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Prospects Found"
          value={summary.total_prospects || 0}
          sub="venues & events"
          icon={Users}
          color="blue"
        />
        <StatCard
          label="Pitches Sent"
          value={summary.total_pitches_sent || 0}
          sub="personalized outreach"
          icon={Mail}
          color="indigo"
        />
        <StatCard
          label="Response Rate"
          value={`${summary.overall_response_rate || 0}%`}
          sub="venues replied"
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          label="Shows Booked"
          value={summary.total_bookings || 0}
          sub={summary.total_bookings > 0 ? `avg $${summary.avg_proposed_rate}/show` : 'keep pitching!'}
          icon={Calendar}
          color="amber"
        />
      </div>

      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white mb-4">Your 4-Agent Pipeline</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <AgentCard
            number="1"
            name="Market Research"
            description="Discovers venues, researches rates, analyzes your competition"
            status="Ready to run"
            to="/research"
            icon={Search}
          />
          <AgentCard
            number="2"
            name="Pitch Generator"
            description="Creates personalized outreach for each venue, optimized for conversion"
            status={summary.total_pitches_sent > 0 ? `${summary.total_pitches_sent} pitches sent` : 'Ready'}
            to="/pitches"
            icon={Mail}
          />
          <AgentCard
            number="3"
            name="Analytics & Learning"
            description="Analyzes what's working and refines strategy with each round"
            status={analytics ? 'Last run: recently' : 'Run after pitches'}
            to="/analytics"
            icon={BarChart3}
          />
          <AgentCard
            number="4"
            name="Follow-Up Engine"
            description="Auto-sequences follow-ups on day 3, 7, and 14 for no-response venues"
            status={dueFollowups.length > 0 ? `${dueFollowups.length} due now` : 'Monitoring'}
            to="/followups"
            icon={Bell}
          />
        </div>
      </div>

      {analytics?.ai_insights && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Zap size={16} className="text-indigo-400" />
            <h3 className="text-white font-semibold">AI Insights</h3>
            <span className="text-xs text-gray-500">from Agent 3</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-1">
              <p className="text-gray-400 text-xs mb-1 uppercase tracking-wide">Top Insight</p>
              <p className="text-white text-sm">{analytics.ai_insights.top_insight}</p>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-2 uppercase tracking-wide">Best Channels</p>
              <div className="flex flex-wrap gap-2">
                {(analytics.ai_insights.focus_channels || []).map(c => (
                  <span key={c} className="px-2 py-1 bg-indigo-600/10 border border-indigo-600/20 rounded text-indigo-400 text-xs">{c}</span>
                ))}
              </div>
            </div>
            <div>
              <p className="text-gray-400 text-xs mb-2 uppercase tracking-wide">Priority Actions</p>
              <ul className="space-y-1">
                {(analytics.ai_insights.recommendations || []).slice(0, 2).map((r, i) => (
                  <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                    <span className="text-indigo-400 flex-shrink-0">→</span>
                    {r.action}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
