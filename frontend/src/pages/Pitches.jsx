import { useState, useEffect } from 'react'
import { prospectsApi, pitchesApi, responsesApi } from '../api/client'
import { Mail, Loader2, Send, Check, ChevronDown, ChevronUp, X } from 'lucide-react'

const RESPONSE_TYPES = ['interested', 'booked', 'negotiating', 'maybe', 'not_interested']
const RESPONSE_COLORS = {
  interested: 'text-blue-400',
  booked: 'text-green-400',
  negotiating: 'text-amber-400',
  maybe: 'text-indigo-400',
  not_interested: 'text-red-400',
}

function PitchCard({ pitch, onSend, onRecordResponse, sent }) {
  const [expanded, setExpanded] = useState(false)
  const [responseType, setResponseType] = useState('')
  const [responseText, setResponseText] = useState('')
  const [recording, setRecording] = useState(false)

  async function handleRecord() {
    if (!responseType) return
    setRecording(true)
    try {
      await onRecordResponse(pitch.id, pitch.prospect_id, responseType, responseText)
    } finally {
      setRecording(false)
    }
  }

  const isBooked = pitch.status === 'booked'
  const hasResponse = pitch.status === 'responded' || isBooked

  return (
    <div className={`bg-gray-900 border rounded-xl overflow-hidden transition-all ${
      isBooked ? 'border-green-600/40' : hasResponse ? 'border-indigo-600/30' : 'border-gray-800'
    }`}>
      <div className="p-4 flex items-start gap-3">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5 ${
          isBooked ? 'bg-green-600/20 text-green-400' :
          hasResponse ? 'bg-indigo-600/20 text-indigo-400' :
          sent ? 'bg-blue-600/20 text-blue-400' : 'bg-gray-800 text-gray-400'
        }`}>
          {isBooked ? <Check size={14} /> : <Mail size={14} />}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-white text-sm font-medium truncate">{pitch.prospect_name}</p>
              <p className="text-gray-500 text-xs">{pitch.venue_type} · {pitch.venue_location}</p>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${
                isBooked ? 'bg-green-600/20 text-green-400' :
                hasResponse ? 'bg-indigo-600/20 text-indigo-400' :
                sent ? 'bg-blue-600/20 text-blue-400' : 'bg-gray-800 text-gray-400'
              }`}>
                {pitch.status}
              </span>
              <span className="text-gray-500 text-xs">${pitch.proposed_rate}/show</span>
            </div>
          </div>
          <p className="text-gray-400 text-xs mt-1 font-medium">{pitch.subject}</p>
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
          <pre className="text-gray-300 text-xs whitespace-pre-wrap font-sans leading-relaxed bg-gray-800/50 rounded-lg p-4 mb-4 max-h-60 overflow-y-auto">
            {pitch.body}
          </pre>

          {!sent && pitch.status === 'draft' && (
            <button
              onClick={() => onSend(pitch.id)}
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <Send size={14} />
              Mark as Sent
            </button>
          )}

          {sent && !hasResponse && (
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-gray-400 text-xs mb-2 font-medium">Record Response</p>
              <div className="flex gap-2 flex-wrap mb-2">
                {RESPONSE_TYPES.map(t => (
                  <button
                    key={t}
                    onClick={() => setResponseType(t)}
                    className={`px-2.5 py-1 rounded-lg text-xs capitalize transition-colors ${
                      responseType === t
                        ? `bg-gray-700 ${RESPONSE_COLORS[t]} font-medium`
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {t.replace('_', ' ')}
                  </button>
                ))}
              </div>
              {responseType && (
                <>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-white text-xs placeholder-gray-600 focus:outline-none focus:border-indigo-500 mb-2"
                    placeholder="Their reply (optional)..."
                    value={responseText}
                    onChange={e => setResponseText(e.target.value)}
                  />
                  <button
                    onClick={handleRecord}
                    disabled={recording}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs rounded-lg transition-colors"
                  >
                    {recording ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                    Record
                  </button>
                </>
              )}
            </div>
          )}

          {hasResponse && (
            <div className={`text-xs px-3 py-2 rounded-lg ${
              isBooked ? 'bg-green-600/10 text-green-400' : 'bg-indigo-600/10 text-indigo-400'
            }`}>
              {isBooked ? '🎉 Booked!' : 'Response recorded — check Analytics for insights'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function Pitches() {
  const profileId = localStorage.getItem('profileId')
  const [prospects, setProspects] = useState([])
  const [pitches, setPitches] = useState([])
  const [selected, setSelected] = useState([])
  const [proposedRate, setProposedRate] = useState('')
  const [generating, setGenerating] = useState(false)
  const [sending, setSending] = useState(false)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('pitches')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      prospectsApi.list(profileId, { status: 'new' }),
      pitchesApi.list(profileId),
    ]).then(([p, pi]) => {
      setProspects(p)
      setPitches(pi)
    }).finally(() => setLoading(false))
  }, [profileId])

  function toggleSelect(id) {
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  }

  function selectAll() {
    if (selected.length === prospects.length) {
      setSelected([])
    } else {
      setSelected(prospects.map(p => p.id))
    }
  }

  async function handleGenerate() {
    if (selected.length === 0) return
    setGenerating(true)
    setError('')
    try {
      const result = await pitchesApi.generate({
        profile_id: parseInt(profileId),
        prospect_ids: selected,
        proposed_rate: proposedRate ? parseFloat(proposedRate) : null,
      })
      setPitches(prev => [...result.pitches, ...prev])
      setSelected([])
      setTab('pitches')
      const updatedProspects = await prospectsApi.list(profileId, { status: 'new' })
      setProspects(updatedProspects)
    } catch (e) {
      setError('Failed to generate pitches. Ensure ANTHROPIC_API_KEY is set.')
    } finally {
      setGenerating(false)
    }
  }

  async function handleSend(pitchId) {
    await pitchesApi.send([pitchId])
    setPitches(prev => prev.map(p => p.id === pitchId ? { ...p, status: 'sent' } : p))
  }

  async function handleSendAll() {
    const draftIds = pitches.filter(p => p.status === 'draft').map(p => p.id)
    if (!draftIds.length) return
    setSending(true)
    await pitchesApi.send(draftIds)
    setPitches(prev => prev.map(p => draftIds.includes(p.id) ? { ...p, status: 'sent' } : p))
    setSending(false)
  }

  async function handleResponse(pitchId, prospectId, type, text) {
    await responsesApi.record({ pitch_id: pitchId, prospect_id: prospectId, response_type: type, response_text: text })
    setPitches(prev => prev.map(p => p.id === pitchId ? { ...p, status: type === 'booked' ? 'booked' : 'responded' } : p))
  }

  const draftPitches = pitches.filter(p => p.status === 'draft')
  const sentPitches = pitches.filter(p => p.status !== 'draft')

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
          <h1 className="text-2xl font-bold text-white">Pitches</h1>
          <p className="text-gray-400 text-sm mt-1">Agent 2 — generate & track personalized outreach</p>
        </div>
        <div className="flex items-center gap-3">
          {draftPitches.length > 0 && (
            <button
              onClick={handleSendAll}
              disabled={sending}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {sending ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
              Send All ({draftPitches.length})
            </button>
          )}
        </div>
      </div>

      <div className="flex gap-1 mb-6">
        {['generate', 'pitches'].map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
              tab === t ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
            }`}
          >
            {t === 'generate' ? `Generate New (${prospects.length} prospects)` : `All Pitches (${pitches.length})`}
          </button>
        ))}
      </div>

      {tab === 'generate' && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <button
                onClick={selectAll}
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                {selected.length === prospects.length ? 'Deselect all' : 'Select all'}
              </button>
              <span className="text-gray-500 text-xs">{selected.length} selected</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-gray-400 text-xs">Proposed rate:</span>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-xs">$</span>
                  <input
                    type="number"
                    className="w-24 bg-gray-800 border border-gray-700 rounded pl-6 pr-3 py-1.5 text-white text-xs focus:outline-none focus:border-indigo-500"
                    placeholder="400"
                    value={proposedRate}
                    onChange={e => setProposedRate(e.target.value)}
                  />
                </div>
              </div>
              <button
                onClick={handleGenerate}
                disabled={selected.length === 0 || generating}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
              >
                {generating ? <Loader2 size={14} className="animate-spin" /> : <Mail size={14} />}
                {generating ? `Generating ${selected.length} pitches...` : `Generate ${selected.length} Pitches`}
              </button>
            </div>
          </div>

          {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

          {generating && (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 text-center mb-4">
              <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-white">Agent 2 is crafting personalized pitches...</p>
              <p className="text-gray-400 text-sm">This may take a moment for larger batches</p>
            </div>
          )}

          {prospects.length === 0 ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
              <Mail size={40} className="text-gray-600 mx-auto mb-4" />
              <p className="text-white font-medium mb-2">No new prospects to pitch</p>
              <p className="text-gray-400 text-sm">Run Market Research first, or all prospects have been pitched already.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {prospects.map(p => (
                <button
                  key={p.id}
                  onClick={() => toggleSelect(p.id)}
                  className={`text-left p-4 rounded-xl border transition-all ${
                    selected.includes(p.id)
                      ? 'border-indigo-500 bg-indigo-600/10'
                      : 'border-gray-800 bg-gray-900 hover:border-gray-700'
                  }`}
                >
                  <div className="flex items-start justify-between mb-1">
                    <p className="text-white text-sm font-medium">{p.name}</p>
                    <div className={`w-4 h-4 rounded border flex-shrink-0 flex items-center justify-center transition-colors ${
                      selected.includes(p.id) ? 'border-indigo-500 bg-indigo-600' : 'border-gray-700'
                    }`}>
                      {selected.includes(p.id) && <Check size={10} className="text-white" />}
                    </div>
                  </div>
                  <p className="text-gray-500 text-xs">{p.type} · {p.location}</p>
                  <p className="text-green-400 text-xs mt-1">${p.typical_pay_min}–${p.typical_pay_max}/show</p>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'pitches' && (
        <div>
          {pitches.length === 0 ? (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
              <Mail size={40} className="text-gray-600 mx-auto mb-4" />
              <p className="text-white font-medium mb-2">No pitches yet</p>
              <p className="text-gray-400 text-sm">Switch to "Generate New" to create your first pitches.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {draftPitches.length > 0 && (
                <div>
                  <p className="text-gray-500 text-xs uppercase tracking-wide mb-2">Drafts — Review & Send</p>
                  {draftPitches.map(p => (
                    <PitchCard key={p.id} pitch={p} onSend={handleSend} onRecordResponse={handleResponse} sent={false} />
                  ))}
                </div>
              )}
              {sentPitches.length > 0 && (
                <div>
                  <p className="text-gray-500 text-xs uppercase tracking-wide mb-2 mt-4">Sent Pitches</p>
                  {sentPitches.map(p => (
                    <PitchCard key={p.id} pitch={p} onSend={handleSend} onRecordResponse={handleResponse} sent={true} />
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
