import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const profilesApi = {
  create: (data) => api.post('/profiles', data).then(r => r.data),
  list: () => api.get('/profiles').then(r => r.data),
  get: (id) => api.get(`/profiles/${id}`).then(r => r.data),
  update: (id, data) => api.put(`/profiles/${id}`, data).then(r => r.data),
}

export const marketResearchApi = {
  run: (profileId) => api.post('/market-research/run', { profile_id: profileId }).then(r => r.data),
  getLatest: (profileId) => api.get(`/market-research/${profileId}`).then(r => r.data),
}

export const prospectsApi = {
  list: (profileId, params) => api.get(`/prospects/${profileId}`, { params }).then(r => r.data),
  create: (data) => api.post('/prospects', data).then(r => r.data),
  updateStatus: (id, status) => api.put(`/prospects/${id}/status`, { status }).then(r => r.data),
  delete: (id) => api.delete(`/prospects/${id}`).then(r => r.data),
}

export const pitchesApi = {
  generate: (data) => api.post('/pitches/generate', data).then(r => r.data),
  list: (profileId, params) => api.get(`/pitches/${profileId}`, { params }).then(r => r.data),
  send: (pitchIds) => api.post('/pitches/send', { pitch_ids: pitchIds }).then(r => r.data),
  delete: (id) => api.delete(`/pitches/${id}`).then(r => r.data),
}

export const responsesApi = {
  record: (data) => api.post('/responses', data).then(r => r.data),
  list: (profileId) => api.get(`/responses/${profileId}`).then(r => r.data),
  handleObjection: (pitchId, type, text) =>
    api.post(`/responses/handle-objection?pitch_id=${pitchId}&objection_type=${encodeURIComponent(type)}&objection_text=${encodeURIComponent(text)}`).then(r => r.data),
}

export const analyticsApi = {
  run: (profileId) => api.post(`/analytics/run/${profileId}`).then(r => r.data),
  get: (profileId) => api.get(`/analytics/${profileId}`).then(r => r.data),
  getTrend: (profileId) => api.get(`/analytics/${profileId}/trend`).then(r => r.data),
}

export const followupsApi = {
  generate: (profileId) => api.post('/followups/generate', { profile_id: profileId }).then(r => r.data),
  list: (profileId, params) => api.get(`/followups/${profileId}`, { params }).then(r => r.data),
  getDue: (profileId) => api.get(`/followups/${profileId}/due`).then(r => r.data),
  markSent: (id) => api.post(`/followups/${id}/send`).then(r => r.data),
  cancel: (id) => api.post(`/followups/${id}/cancel`).then(r => r.data),
}
