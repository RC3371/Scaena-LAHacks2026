import { useState, useEffect } from 'react'
import { analyticsApi } from '../api/client'
import { BarChart3, Loader2, RefreshCw, Zap, TrendingUp, Target, AlertTriangle } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts'

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 text-xs">
      <p className="text-white font-medium mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value}{p.name.includes('Rate') ? '%' : ''}</p>
      ))}
    </div>
  )
}

export default function Analytics() {
  const profileId = localStorage.getItem('profileId')
  const [analytics, setAnalytics] = useState(null)
  const [trend, setTrend] = useState([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)

  useEffect(() => {
    Promise.all([
      analyticsApi.get(profileId).catch(() => null),
      analyticsApi.getTrend(profileId).catch(() => []),
    ]).then(([a, t]) => {
      setAnalytics(a)
      setTrend(t)
    }).finally(() => setLoading(false))
  }, [profileId])

  async function runAnalytics() {
    setRunning(true)
    try {
      const result = await analyticsApi.run(profileId)
      setAnalytics(result)
      const t = await analyticsApi.getTrend(profileId)
      setTrend(t)
    } finally {
      setRunning(false)
    }
  }

  const venueChartData = analytics?.venue_performance
    ? Object.entries(analytics.venue_performance).map(([type, data]) => ({
        name: type.replace(' Event', '').replace(' Venue', ''),
        'Response Rate': data.response_rate,
        'Booking Rate': data.booking_rate,
        Sent: data.sent,
      }))
    : []

  const responseBreakdown = analytics?.response_breakdown
    ? Object.entries(analytics.response_breakdown).map(([type, count]) => ({
        name: type.replace('_', ' '),
        value: count,
      }))
    : []

  const trendData = trend.map((t, i) => ({
    week: `Week ${i + 1}`,
    'Response Rate': t.overall_response_rate,
    Bookings: t.total_bookings,
    'Pitches Sent': t.total_pitches_sent,
  }))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <p className="text-gray-400 text-sm mt-1">Agent 3 — learn what's working, optimize your strategy</p>
        </div>
        <button
          onClick={runAnalytics}
          disabled={running}
          className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors text-sm"
        >
          {running ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {running ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {!analytics && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <BarChart3 size={40} className="text-gray-600 mx-auto mb-4" />
          <p className="text-white font-medium mb-2">No analytics yet</p>
          <p className="text-gray-400 text-sm">Send pitches and record responses, then run Agent 3 analysis.</p>
        </div>
      )}

      {analytics && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: 'Pitches Sent', value: analytics.summary?.total_pitches_sent || 0, color: 'text-blue-400' },
              { label: 'Response Rate', value: `${analytics.summary?.overall_response_rate || 0}%`, color: 'text-green-400' },
              { label: 'Shows Booked', value: analytics.summary?.total_bookings || 0, color: 'text-indigo-400' },
              { label: 'Interested Leads', value: analytics.summary?.interested_leads || 0, color: 'text-amber-400' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                <p className="text-gray-500 text-xs mb-1">{label}</p>
                <p className={`text-2xl font-bold ${color}`}>{value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {venueChartData.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h3 className="text-white font-semibold text-sm mb-4">Response Rate by Venue Type</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={venueChartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="Response Rate" fill="#6366f1" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Booking Rate" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {responseBreakdown.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h3 className="text-white font-semibold text-sm mb-4">Response Breakdown</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={responseBreakdown}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {responseBreakdown.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend
                      formatter={(value) => <span style={{ color: '#9ca3af', fontSize: 11 }}>{value}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {trendData.length > 1 && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={16} className="text-green-400" />
                <h3 className="text-white font-semibold text-sm">Performance Trend</h3>
                <span className="text-gray-500 text-xs">— compounding improvement over time</span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={trendData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="week" tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="Response Rate" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1' }} />
                  <Line type="monotone" dataKey="Bookings" stroke="#22c55e" strokeWidth={2} dot={{ fill: '#22c55e' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {analytics.ai_insights && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <div className="flex items-center gap-2 mb-5">
                <Zap size={16} className="text-indigo-400" />
                <h3 className="text-white font-semibold">AI Strategy Recommendations</h3>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div>
                  <p className="text-gray-500 text-xs uppercase tracking-wide mb-2">Top Insight</p>
                  <p className="text-white text-sm">{analytics.ai_insights.top_insight}</p>

                  {analytics.ai_insights.rate_analysis && (
                    <div className="mt-4">
                      <p className="text-gray-500 text-xs uppercase tracking-wide mb-2">Rate Analysis</p>
                      <p className="text-amber-400 text-xs font-medium capitalize">{analytics.ai_insights.rate_analysis.current_rate_assessment}</p>
                      <p className="text-gray-300 text-xs mt-1">{analytics.ai_insights.rate_analysis.suggested_adjustment}</p>
                    </div>
                  )}
                </div>

                <div>
                  <p className="text-gray-500 text-xs uppercase tracking-wide mb-2">Winning Angles</p>
                  <ul className="space-y-1.5">
                    {(analytics.ai_insights.effective_angles || []).map((angle, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-gray-300">
                        <Target size={12} className="text-indigo-400 flex-shrink-0 mt-0.5" />
                        {angle}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <p className="text-gray-500 text-xs uppercase tracking-wide mb-2">Action Items</p>
                  <ul className="space-y-2">
                    {(analytics.ai_insights.recommendations || []).map((rec, i) => (
                      <li key={i} className="text-xs">
                        <span className={`inline-block px-1.5 py-0.5 rounded text-xs mr-1.5 ${
                          rec.priority === 'high' ? 'bg-red-600/20 text-red-400' :
                          rec.priority === 'medium' ? 'bg-amber-600/20 text-amber-400' :
                          'bg-gray-700 text-gray-400'
                        }`}>{rec.priority}</span>
                        <span className="text-gray-300">{rec.action}</span>
                        <span className="text-green-400 block mt-0.5 ml-0">{rec.expected_impact}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {analytics.ai_insights.warning_flags?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-gray-800">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle size={14} className="text-amber-400" />
                    <p className="text-amber-400 text-xs font-medium">Watch Out</p>
                  </div>
                  {analytics.ai_insights.warning_flags.map((flag, i) => (
                    <p key={i} className="text-gray-400 text-xs">{flag}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
