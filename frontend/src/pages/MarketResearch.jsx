import { useState, useEffect } from 'react'
import { marketResearchApi } from '../api/client'
import { Search, Loader2, TrendingUp, MapPin, DollarSign, Zap, RefreshCw } from 'lucide-react'

export default function MarketResearch() {
  const profileId = localStorage.getItem('profileId')
  const [research, setResearch] = useState(null)
  const [loading, setLoading] = useState(false)
  const [fetchingExisting, setFetchingExisting] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    marketResearchApi.getLatest(profileId)
      .then(r => setResearch(r.data))
      .catch(() => {})
      .finally(() => setFetchingExisting(false))
  }, [profileId])

  async function runResearch() {
    setLoading(true)
    setError('')
    try {
      const result = await marketResearchApi.run(profileId)
      setResearch(result.data)
    } catch (e) {
      setError('Research failed. Check that ANTHROPIC_API_KEY is set.')
    } finally {
      setLoading(false)
    }
  }

  if (fetchingExisting) {
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
          <h1 className="text-2xl font-bold text-white">Market Research</h1>
          <p className="text-gray-400 text-sm mt-1">Agent 1 — venue discovery, rate analysis, competitive positioning</p>
        </div>
        <button
          onClick={runResearch}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors text-sm"
        >
          {loading ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {loading ? 'Researching...' : research ? 'Re-run Research' : 'Run Market Research'}
        </button>
      </div>

      {error && (
        <div className="mb-6 bg-red-900/20 border border-red-700 rounded-xl p-4 text-red-400 text-sm">{error}</div>
      )}

      {loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center mb-6">
          <div className="w-10 h-10 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-white font-medium">Agent 1 is researching your market...</p>
          <p className="text-gray-400 text-sm mt-1">Analyzing rates, finding venues, assessing competition</p>
        </div>
      )}

      {!research && !loading && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <Search size={40} className="text-gray-600 mx-auto mb-4" />
          <p className="text-white font-medium mb-2">No research yet</p>
          <p className="text-gray-400 text-sm">Run Agent 1 to discover market rates and venue opportunities tailored to your profile.</p>
        </div>
      )}

      {research && !loading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <DollarSign size={16} className="text-green-400" />
                <span className="text-gray-400 text-sm">Market Rates</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500 text-xs">Entry Level</span>
                  <span className="text-white text-xs">{research.market_insights?.market_rates?.entry_level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 text-xs">Mid Level</span>
                  <span className="text-white text-xs">{research.market_insights?.market_rates?.mid_level}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 text-xs">Established</span>
                  <span className="text-white text-xs">{research.market_insights?.market_rates?.established}</span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-800">
                <p className="text-indigo-400 text-xs font-medium">Recommended for you</p>
                <p className="text-white text-sm mt-1">
                  ${research.market_insights?.recommended_rate_min}–${research.market_insights?.recommended_rate_max}/show
                </p>
              </div>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp size={16} className="text-indigo-400" />
                <span className="text-gray-400 text-sm">Competitive Position</span>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500 text-xs">Market Average</span>
                  <span className="text-white text-xs">${research.competitive_analysis?.average_market_rate}/show</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 text-xs">Your Rate</span>
                  <span className="text-white text-xs">${research.competitive_analysis?.your_current_rate}/show</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 text-xs">Positioning</span>
                  <span className={`text-xs capitalize ${
                    research.competitive_analysis?.positioning === 'at market' ? 'text-green-400' :
                    research.competitive_analysis?.positioning === 'above market' ? 'text-amber-400' : 'text-indigo-400'
                  }`}>
                    {research.competitive_analysis?.positioning}
                  </span>
                </div>
              </div>
              <div className="mt-3 pt-3 border-t border-gray-800">
                <p className="text-gray-400 text-xs">{research.competitive_analysis?.recommendation}</p>
              </div>
            </div>

            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Zap size={16} className="text-amber-400" />
                <span className="text-gray-400 text-sm">Key Insights</span>
              </div>
              <ul className="space-y-2">
                {(research.key_insights || []).map((insight, i) => (
                  <li key={i} className="text-xs text-gray-300 flex items-start gap-2">
                    <span className="text-amber-400 flex-shrink-0 mt-0.5">•</span>
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div>
            <h2 className="text-lg font-semibold text-white mb-4">
              Venue Opportunities
              {research.venue_opportunities && (
                <span className="text-gray-500 text-sm font-normal ml-2">({research.venue_opportunities.length} types found)</span>
              )}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {(research.venue_opportunities || []).map((venue, i) => (
                <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-white font-medium text-sm">{venue.type}</h3>
                    <span className="text-xs text-gray-500 bg-gray-800 px-2 py-0.5 rounded">{venue.fit_score}/10 fit</span>
                  </div>
                  <p className="text-green-400 text-sm font-medium mb-2">
                    ${venue.typical_pay_min}–${venue.typical_pay_max}/show
                  </p>
                  <p className="text-gray-500 text-xs mb-2">{venue.booking_frequency}</p>
                  <div className="flex flex-wrap gap-1 mb-2">
                    {(venue.examples || []).slice(0, 3).map((ex, j) => (
                      <span key={j} className="text-xs text-gray-400 bg-gray-800 px-2 py-0.5 rounded">{ex}</span>
                    ))}
                  </div>
                  {venue.notes && <p className="text-gray-500 text-xs">{venue.notes}</p>}
                </div>
              ))}
            </div>
          </div>

          {research.growth_opportunities && (
            <div>
              <h2 className="text-lg font-semibold text-white mb-4">Growth Opportunities</h2>
              <div className="space-y-3">
                {research.growth_opportunities.map((opp, i) => (
                  <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-white text-sm font-medium">{opp.opportunity}</p>
                      <p className="text-green-400 text-xs mt-1">{opp.potential_revenue_increase}</p>
                    </div>
                    <span className={`ml-4 text-xs px-2.5 py-1 rounded-full border ${
                      opp.effort === 'low' ? 'border-green-600/40 text-green-400 bg-green-600/10' :
                      opp.effort === 'medium' ? 'border-amber-600/40 text-amber-400 bg-amber-600/10' :
                      'border-red-600/40 text-red-400 bg-red-600/10'
                    }`}>
                      {opp.effort} effort
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {research.discovered_prospects && research.discovered_prospects.length > 0 && (
            <div className="bg-indigo-600/10 border border-indigo-600/30 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <MapPin size={16} className="text-indigo-400" />
                <p className="text-white font-medium">
                  {research.discovered_prospects.length} venues added to your Prospects list
                </p>
              </div>
              <p className="text-indigo-300/70 text-sm">
                Agent 1 discovered and saved these venues. Go to Prospects to review and select which to pitch.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
