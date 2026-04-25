import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { profilesApi } from '../api/client'
import { Zap, ChevronRight, Loader2 } from 'lucide-react'

const ENTERTAINER_TYPES = [
  'comedian', 'rapper', 'singer', 'musician', 'dj',
  'public speaker', 'motivational speaker', 'magician', 'band', 'podcast creator', 'content creator',
]

const steps = ['Your Profile', 'Experience & Rates', 'Online Presence']

export default function Onboarding() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    name: '',
    entertainer_type: '',
    genre_style: '',
    location: '',
    touring_region: '',
    experience_years: '',
    shows_count: '',
    rate_min: '',
    rate_max: '',
    instagram_followers: '',
    instagram_url: '',
    youtube_url: '',
    bio: '',
  })

  function update(field, value) {
    setForm(f => ({ ...f, [field]: value }))
  }

  async function handleSubmit() {
    setLoading(true)
    setError('')
    try {
      const payload = {
        ...form,
        experience_years: parseInt(form.experience_years) || 0,
        shows_count: parseInt(form.shows_count) || 0,
        rate_min: parseFloat(form.rate_min) || 0,
        rate_max: parseFloat(form.rate_max) || 0,
        instagram_followers: parseInt(form.instagram_followers) || 0,
      }
      const profile = await profilesApi.create(payload)
      localStorage.setItem('profileId', profile.id)
      navigate('/')
    } catch (e) {
      setError('Failed to create profile. Make sure the backend is running.')
    } finally {
      setLoading(false)
    }
  }

  function useDemoProfile() {
    const existingId = localStorage.getItem('profileId')
    if (existingId) {
      navigate('/')
      return
    }
    localStorage.setItem('profileId', '1')
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-indigo-600 rounded-2xl mb-4">
            <Zap size={28} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">GigAI</h1>
          <p className="text-gray-400 mt-1">AI-powered booking automation for entertainers</p>
        </div>

        <div className="bg-gray-900 rounded-2xl border border-gray-800 p-8">
          <div className="flex items-center gap-2 mb-8">
            {steps.map((s, i) => (
              <div key={i} className="flex items-center gap-2 flex-1">
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                  i <= step ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-500'
                }`}>
                  {i + 1}
                </div>
                <span className={`text-xs font-medium hidden sm:block ${i <= step ? 'text-white' : 'text-gray-500'}`}>{s}</span>
                {i < steps.length - 1 && <div className={`flex-1 h-px ${i < step ? 'bg-indigo-600' : 'bg-gray-700'}`} />}
              </div>
            ))}
          </div>

          {step === 0 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white">Tell us about yourself</h2>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Your Name *</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                  placeholder="Alex Rivera"
                  value={form.name}
                  onChange={e => update('name', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Entertainer Type *</label>
                <select
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-indigo-500"
                  value={form.entertainer_type}
                  onChange={e => update('entertainer_type', e.target.value)}
                >
                  <option value="">Select type...</option>
                  {ENTERTAINER_TYPES.map(t => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Genre / Style</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                  placeholder="Dark humor & storytelling"
                  value={form.genre_style}
                  onChange={e => update('genre_style', e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">City, State</label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    placeholder="Los Angeles, CA"
                    value={form.location}
                    onChange={e => update('location', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Touring Region</label>
                  <input
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    placeholder="West Coast"
                    value={form.touring_region}
                    onChange={e => update('touring_region', e.target.value)}
                  />
                </div>
              </div>
              <button
                onClick={() => setStep(1)}
                disabled={!form.name || !form.entertainer_type}
                className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors"
              >
                Next <ChevronRight size={16} />
              </button>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white">Experience & Rates</h2>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Years Experience</label>
                  <input
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    placeholder="3"
                    value={form.experience_years}
                    onChange={e => update('experience_years', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Total Shows</label>
                  <input
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    placeholder="50"
                    value={form.shows_count}
                    onChange={e => update('shows_count', e.target.value)}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Min Rate ($/show)</label>
                  <input
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    placeholder="300"
                    value={form.rate_min}
                    onChange={e => update('rate_min', e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Max Rate ($/show)</label>
                  <input
                    type="number"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    placeholder="500"
                    value={form.rate_max}
                    onChange={e => update('rate_max', e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Bio (for pitch personalization)</label>
                <textarea
                  rows={3}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 resize-none"
                  placeholder="Stand-up comedian known for dark humor and storytelling..."
                  value={form.bio}
                  onChange={e => update('bio', e.target.value)}
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => setStep(0)}
                  className="flex-1 border border-gray-700 text-gray-300 hover:text-white py-2.5 rounded-lg transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(2)}
                  className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 rounded-lg transition-colors"
                >
                  Next <ChevronRight size={16} />
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-white">Online Presence</h2>
              <p className="text-gray-400 text-sm">Used to personalize pitches with your social proof.</p>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Instagram Followers</label>
                <input
                  type="number"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                  placeholder="14200"
                  value={form.instagram_followers}
                  onChange={e => update('instagram_followers', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Instagram URL</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                  placeholder="https://instagram.com/yourhandle"
                  value={form.instagram_url}
                  onChange={e => update('instagram_url', e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">YouTube URL</label>
                <input
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                  placeholder="https://youtube.com/@yourhandle"
                  value={form.youtube_url}
                  onChange={e => update('youtube_url', e.target.value)}
                />
              </div>
              {error && <p className="text-red-400 text-sm">{error}</p>}
              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="flex-1 border border-gray-700 text-gray-300 hover:text-white py-2.5 rounded-lg transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors"
                >
                  {loading ? <Loader2 size={16} className="animate-spin" /> : null}
                  {loading ? 'Creating...' : 'Launch GigAI'}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="mt-4 text-center">
          <button
            onClick={useDemoProfile}
            className="text-indigo-400 hover:text-indigo-300 text-sm underline"
          >
            Use demo profile instead (Alex Rivera – Comedian)
          </button>
        </div>
      </div>
    </div>
  )
}
