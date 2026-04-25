const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`GET ${path} failed: ${r.status}`)
  return r.json()
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`POST ${path} failed: ${r.status}`)
  return r.json()
}

async function put<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`PUT ${path} failed: ${r.status}`)
  return r.json()
}

export const PROFILE_ID = 1

export const api = {
  profile: () => get<Profile>(`/profiles/${PROFILE_ID}`),

  analytics: () => get<Analytics>(`/analytics/${PROFILE_ID}`),
  runAnalytics: () => post<Analytics>(`/analytics/run/${PROFILE_ID}`),
  analyticsTrend: () => get<TrendPoint[]>(`/analytics/${PROFILE_ID}/trend`),

  marketResearch: () => get<MarketResearchResult>(`/market-research/${PROFILE_ID}`),
  runMarketResearch: () => post<MarketResearchResult>(`/market-research/run`, { profile_id: PROFILE_ID }),

  prospects: (status?: string) => get<Prospect[]>(`/prospects/${PROFILE_ID}${status ? `?status=${status}` : ''}`),
  updateProspectStatus: (id: number, status: string) => put<Prospect>(`/prospects/${id}/status`, { status }),

  pitches: (status?: string) => get<Pitch[]>(`/pitches/${PROFILE_ID}${status ? `?status=${status}` : ''}`),
  generatePitches: (prospectIds: number[], rate?: number) =>
    post<{ pitches: Pitch[]; count: number }>(`/pitches/generate`, {
      profile_id: PROFILE_ID,
      prospect_ids: prospectIds,
      proposed_rate: rate,
    }),
  sendPitches: (ids: number[]) => post<void>(`/pitches/send`, { pitch_ids: ids }),

  responses: () => get<Response[]>(`/responses/${PROFILE_ID}`),
  recordResponse: (pitchId: number, prospectId: number, type: string, text?: string) =>
    post<Response>(`/responses`, { pitch_id: pitchId, prospect_id: prospectId, response_type: type, response_text: text }),

  followups: (status?: string) => get<FollowUp[]>(`/followups/${PROFILE_ID}${status ? `?status=${status}` : ''}`),
  generateFollowups: () => post<{ scheduled: FollowUp[]; count: number }>(`/followups/generate`, { profile_id: PROFILE_ID }),
  sendFollowup: (id: number) => post<void>(`/followups/${id}/send`),
  cancelFollowup: (id: number) => post<void>(`/followups/${id}/cancel`),
  dueFollowups: () => get<FollowUp[]>(`/followups/${PROFILE_ID}/due`),
}

// --- Types ---

export interface Profile {
  id: number
  name: string
  entertainer_type: string
  genre_style: string
  location: string
  rate_min: number
  rate_max: number
  instagram_followers: number
  shows_count: number
  experience_years: number
  youtube_url: string
  created_at: string
}

export interface Analytics {
  summary: {
    total_prospects: number
    total_pitches_sent: number
    total_responses: number
    overall_response_rate: number
    total_bookings: number
    interested_leads: number
    avg_proposed_rate: number
    follow_ups_sent: number
  }
  venue_performance: Record<string, {
    sent: number
    responses: number
    bookings: number
    response_rate: number
    booking_rate: number
  }>
  response_breakdown: Record<string, number>
  ai_insights?: {
    top_insight: string
    effective_angles: string[]
    recommendations: { action: string; expected_impact: string; priority: string }[]
    rate_analysis: { current_rate_assessment: string; suggested_adjustment: string; reasoning: string }
    focus_channels: string[]
    warning_flags: string[]
  }
}

export interface TrendPoint {
  date: string
  total_pitches_sent: number
  overall_response_rate: number
  total_bookings: number
}

export interface MarketResearchResult {
  data: {
    market_insights: {
      recommended_rate_min: number
      recommended_rate_max: number
      pricing_recommendation: string
      market_rates: { entry_level: string; mid_level: string; established: string }
    }
    competitive_analysis: {
      similar_entertainers_count: number
      average_market_rate: number
      your_current_rate: number
      positioning: string
      recommendation: string
    }
    venue_opportunities: { type: string; typical_pay_min: number; typical_pay_max: number; fit_score: number }[]
    key_insights: string[]
    _simulation?: boolean
  }
}

export interface Prospect {
  id: number
  name: string
  type: string
  location: string
  contact_name: string
  contact_email: string
  typical_pay_min: number
  typical_pay_max: number
  status: string
  notes?: string
  created_at: string
}

export interface Pitch {
  id: number
  prospect_id: number
  profile_id: number
  subject: string
  body: string
  proposed_rate: number
  status: string
  sent_at?: string
  created_at: string
  prospect_name?: string
  venue_type?: string
  venue_location?: string
}

export interface Response {
  id: number
  pitch_id: number
  prospect_id: number
  response_type: string
  response_text?: string
  responded_at: string
  venue_name?: string
  venue_type?: string
}

export interface FollowUp {
  id: number
  pitch_id: number
  prospect_id: number
  sequence_number: number
  subject: string
  body: string
  scheduled_for: string
  sent_at?: string
  status: string
  prospect_name?: string
  venue_type?: string
}
