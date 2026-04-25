import { useState, useEffect } from 'react'
import { prospectsApi } from '../api/client'
import { Users, MapPin, DollarSign, Filter, Plus, Trash2 } from 'lucide-react'

const STATUS_COLORS = {
  new: 'bg-gray-700 text-gray-300',
  pitched: 'bg-blue-600/20 text-blue-400',
  responded: 'bg-indigo-600/20 text-indigo-400',
  booked: 'bg-green-600/20 text-green-400',
  declined: 'bg-red-600/20 text-red-400',
  follow_up: 'bg-amber-600/20 text-amber-400',
}

const VENUE_TYPE_ICONS = {
  'Comedy Club': '🎭',
  'Corporate Event': '🏢',
  'College Venue': '🎓',
  'Comedy Festival': '🎪',
  'Concert Hall': '🎵',
  'Default': '📍',
}

export default function Prospects() {
  const profileId = localStorage.getItem('profileId')
  const [prospects, setProspects] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    prospectsApi.list(profileId)
      .then(setProspects)
      .finally(() => setLoading(false))
  }, [profileId])

  async function updateStatus(id, status) {
    const updated = await prospectsApi.updateStatus(id, status)
    setProspects(p => p.map(pr => pr.id === id ? { ...pr, status } : pr))
  }

  async function deleteProspect(id) {
    await prospectsApi.delete(id)
    setProspects(p => p.filter(pr => pr.id !== id))
  }

  const filtered = prospects.filter(p => {
    const matchStatus = filter === 'all' || p.status === filter
    const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || p.type?.toLowerCase().includes(search.toLowerCase())
    return matchStatus && matchSearch
  })

  const counts = prospects.reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1
    return acc
  }, {})

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
          <h1 className="text-2xl font-bold text-white">Prospects</h1>
          <p className="text-gray-400 text-sm mt-1">{prospects.length} venues & opportunities in your pipeline</p>
        </div>
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <span className="bg-green-600/10 text-green-400 px-2.5 py-1 rounded-full border border-green-600/20">
            {counts.booked || 0} booked
          </span>
          <span className="bg-indigo-600/10 text-indigo-400 px-2.5 py-1 rounded-full border border-indigo-600/20">
            {counts.responded || 0} responded
          </span>
          <span className="bg-blue-600/10 text-blue-400 px-2.5 py-1 rounded-full border border-blue-600/20">
            {counts.pitched || 0} pitched
          </span>
        </div>
      </div>

      <div className="flex gap-3 mb-6">
        <input
          className="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm"
          placeholder="Search prospects..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-500" />
          {['all', 'new', 'pitched', 'responded', 'booked', 'declined'].map(s => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                filter === s
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-12 text-center">
          <Users size={40} className="text-gray-600 mx-auto mb-4" />
          <p className="text-white font-medium mb-2">No prospects found</p>
          <p className="text-gray-400 text-sm">Run Market Research (Agent 1) to discover venues automatically.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(prospect => (
            <div key={prospect.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{VENUE_TYPE_ICONS[prospect.type] || VENUE_TYPE_ICONS.Default}</span>
                  <div>
                    <h3 className="text-white font-medium text-sm leading-tight">{prospect.name}</h3>
                    <p className="text-gray-500 text-xs">{prospect.type}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full capitalize flex-shrink-0 ${STATUS_COLORS[prospect.status] || STATUS_COLORS.new}`}>
                  {prospect.status}
                </span>
              </div>

              {prospect.location && (
                <div className="flex items-center gap-1.5 text-gray-500 text-xs mb-2">
                  <MapPin size={11} />
                  {prospect.location}
                </div>
              )}

              <div className="flex items-center gap-1.5 text-gray-400 text-xs mb-2">
                <DollarSign size={11} />
                ${prospect.typical_pay_min}–${prospect.typical_pay_max}/show
              </div>

              {prospect.contact_name && (
                <p className="text-gray-500 text-xs mb-3">Contact: {prospect.contact_name}</p>
              )}

              {prospect.notes && (
                <p className="text-gray-600 text-xs mb-3 italic">{prospect.notes}</p>
              )}

              <div className="mt-auto flex items-center gap-2 pt-3 border-t border-gray-800">
                <select
                  value={prospect.status}
                  onChange={e => updateStatus(prospect.id, e.target.value)}
                  className="flex-1 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 px-2 py-1.5 focus:outline-none"
                >
                  <option value="new">New</option>
                  <option value="pitched">Pitched</option>
                  <option value="responded">Responded</option>
                  <option value="booked">Booked</option>
                  <option value="declined">Declined</option>
                  <option value="follow_up">Follow-Up</option>
                </select>
                <button
                  onClick={() => deleteProspect(prospect.id)}
                  className="p-1.5 text-gray-600 hover:text-red-400 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
