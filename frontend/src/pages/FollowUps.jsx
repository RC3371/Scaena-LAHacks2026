import { useState, useEffect } from 'react'
import { followupsApi } from '../api/client'
import { Bell, Loader2, Send, X, ChevronDown, ChevronUp, RefreshCw, Clock } from 'lucide-react'

function FollowUpCard({ followup, onSend, onCancel }) {
  const [expanded, setExpanded] = useState(false)
  const [sending, setSending] = useState(false)

  const isDue = followup.scheduled_for && new Date(followup.scheduled_for) <= new Date()
  const isSent = followup.status === 'sent'
  const isCancelled = followup.status === 'cancelled'

  async function handleSend() {
    setSending(true)
    try {
      await onSend(followup.id)
    } finally {
      setSending(false)
    }
  }

  const seqColors = ['bg-blue-600/20 text-blue-400', 'bg-indigo-600/20 text-indigo-400', 'bg-amber-600/20 text-amber-400']
  const seqColor = seqColors[(followup.sequence_number - 1) % seqColors.length]

  return (
    <div className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${
      isSent ? 'border-green-600/30 opacity-60' :
      isCancelled ? 'border-gray-700 opacity-40' :
      isDue ? 'border-amber-600/40' : 'border-gray-800'
    }`}>
      <div className="p-4 flex items-start gap-3">
        <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-xs font-bold ${seqColor}`}>
          {followup.sequence_number}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-white text-sm font-medium">{followup.prospect_name}</p>
              <p className="text-gray-500 text-xs">{followup.venue_type} · Follow-up #{followup.sequence_number}</p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {isDue && !isSent && !isCancelled && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-600/20 text-amber-400 border border-amber-600/30">Due Now</span>
              )}
              {isSent && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-green-600/20 text-green-400">Sent</span>
              )}
              {!isDue && !isSent && !isCancelled && (
                <div className="flex items-center gap-1 text-gray-500 text-xs">
                  <Clock size={10} />
                  {new Date(followup.scheduled_for).toLocaleDateString()}
                </div>
              )}
            </div>
          </div>
          <p className="text-gray-400 text-xs mt-1 font-medium truncate">{followup.subject}</p>
        </div>

        <button
          onClick={() => setExpanded(e => !e)}
          className="text-gray-500 hover:text-white transition-colors flex-shrink-0"
        >
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-800 pt-4">
          <pre className="text-gray-300 text-xs whitespace-pre-wrap font-sans leading-relaxed bg-gray-800/50 rounded-lg p-4 mb-4 max-h-48 overflow-y-auto">
            {followup.body}
          </pre>

          {!isSent && !isCancelled && (
            <div className="flex gap-2">
              <button
                onClick={handleSend}
                disabled={sending}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-colors"
              >
                {sending ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
                Mark Sent
              </button>
              <button
                onClick={() => onCancel(followup.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-gray-400 hover:text-red-400 text-xs transition-colors"
              >
                <X size={12} />
                Cancel
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function FollowUps() {
  const profileId = localStorage.getItem('profileId')
  const [followups, setFollowups] = useState([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [tab, setTab] = useState('all')
  const [error, setError] = useState('')

  useEffect(() => {
    followupsApi.list(profileId)
      .then(setFollowups)
      .finally(() => setLoading(false))
  }, [profileId])

  async function handleGenerate() {
    setGenerating(true)
    setError('')
    try {
      const result = await followupsApi.generate(profileId)
      if (result.count > 0) {
        const updated = await followupsApi.list(profileId)
        setFollowups(updated)
      }
    } catch (e) {
      setError('Failed to generate follow-ups. Ensure ANTHROPIC_API_KEY is set.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleSend(id) {
    await followupsApi.markSent(id)
    setFollowups(prev => prev.map(f => f.id === id ? { ...f, status: 'sent' } : f))
  }

  async function handleCancel(id) {
    await followupsApi.cancel(id)
    setFollowups(prev => prev.map(f => f.id === id ? { ...f, status: 'cancelled' } : f))
  }

  const now = new Date()
  const due = followups.filter(f => f.status === 'scheduled' && new Date(f.scheduled_for) <= now)
  const scheduled = followups.filter(f => f.status === 'scheduled' && new Date(f.scheduled_for) > now)
  const sent = followups.filter(f => f.status === 'sent')
  const cancelled = followups.filter(f => f.status === 'cancelled')

  const displayed = tab === 'due' ? due :
    tab === 'scheduled' ? scheduled :
    tab === 'sent' ? sent :
    followups.filter(f => f.status !== 'cancelled')

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
          <h1 className="text-2xl font-bold text-white">Follow-Ups</h1>
          <p className="text-gray-400 text-sm mt-1">Agent 4 — auto-sequences for non-responding venues (day 3, 7, 14)</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium rounded-lg transition-colors text-sm"
        >
          {generating ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
          {generating ? 'Generating...' : 'Generate Follow-Ups'}
        </button>
      </div>

      {due.length > 0 && (
        <div className="mb-6 bg-amber-600/10 border border-amber-600/30 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-1">
            <Bell size={16} className="text-amber-400" />
            <p className="text-white font-medium text-sm">{due.length} follow-up{due.length !== 1 ? 's' : ''} ready to send</p>
          </div>
          <p className="text-amber-400/70 text-xs">These venues haven't responded. Sending today recovers 25-40% of bookings.</p>
        </div>
      )}

      {error && (
        <div className="mb-4 bg-red-900/20 border border-red-700 rounded-xl p-3 text-red-400 text-sm">{error}</div>
      )}

      {generating && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center mb-4">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-white">Agent 4 is crafting follow-up messages...</p>
          <p className="text-gray-400 text-sm">Using different angles than the original pitch</p>
        </div>
      )}

      <div className="flex gap-1 mb-6">
        {[
          { key: 'all', label: `All (${followups.filter(f => f.status !== 'cancelled').length})` },
          { key: 'due', label: `Due Now (${due.length})`, highlight: due.length > 0 },
          { key: 'scheduled', label: `Scheduled (${scheduled.length})` },
          { key: 'sent', label: `Sent (${sent.length})` },
        ].map(({ key, label, highlight }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              tab === key
                ? highlight ? 'bg-amber-600 text-white' : 'bg-indigo-600 text-white'
                : highlight ? 'text-amber-400 hover:bg-amber-600/10' : 'text-gray-400 hover:text-white'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {displayed.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <Bell size={40} className="text-gray-600 mx-auto mb-4" />
          <p className="text-white font-medium mb-2">No follow-ups here</p>
          <p className="text-gray-400 text-sm">
            {tab === 'due' ? 'No follow-ups are due right now — check back after sending pitches.' :
             'Generate follow-ups for pitches that haven\'t received responses yet.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayed.map(f => (
            <FollowUpCard key={f.id} followup={f} onSend={handleSend} onCancel={handleCancel} />
          ))}
        </div>
      )}
    </div>
  )
}
