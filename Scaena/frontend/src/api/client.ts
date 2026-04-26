import axios from "axios";
import type { AgentEvent, Conversation, Entertainer, Insight, Pitch, Venue } from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

export const client = {
  entertainers: {
    active: async () => (await api.get<Entertainer[]>("/entertainers/active")).data,
    get: async (id: string) => (await api.get<Entertainer>(`/entertainers/${id}`)).data,
    update: async (id: string, payload: Partial<Entertainer>) =>
      (await api.put<Entertainer>(`/entertainers/${id}`, payload)).data,
    create: async (payload: Partial<Entertainer>) =>
      (await api.post<Entertainer>("/entertainers", payload)).data,
  },
  venues: {
    list: async (entertainerId: string) =>
      (await api.get<Venue[]>(`/venues/${entertainerId}`)).data,
  },
  outreach: {
    pitches: async (entertainerId: string, status?: string) =>
      (await api.get<Pitch[]>(`/outreach/pitches/${entertainerId}`, { params: { status } })).data,
    updatePitch: async (pitchId: string, payload: Record<string, unknown>) =>
      (await api.patch(`/outreach/pitch/${pitchId}`, payload)).data,
    createPitch: async (payload: {
      entertainer_id: string;
      venue_name: string;
      pitch_subject: string;
      pitch_body: string;
      proposed_rate?: number;
      entertainer_type?: string;
      recipient_email?: string;
      venue_contact_approach?: string;
      status?: string;
    }) => (await api.post("/outreach/pitch", payload)).data,
    generatePitch: async (payload: {
      entertainer_id: string;
      venue_id?: string;
      venue_name?: string;
      venue_type?: string;
      recipient_email?: string;
      venue_contact_approach?: string;
      why_fits?: string;
      source_url?: string;
      specific_examples?: string;
      proposed_rate?: number;
      status?: string;
    }) => (await api.post("/outreach/pitch/generated", payload)).data,
    createRebookPitch: async (payload: {
      entertainer_id: string;
      booking_id: string;
      status?: string;
    }) => (await api.post("/outreach/pitch/rebook", payload)).data,
    regeneratePitch: async (pitchId: string, payload: {
      entertainer_id?: string;
      strategy_instruction?: string;
    }) => (await api.post(`/outreach/pitch/${pitchId}/regenerate`, payload)).data,
    strategyUpdate: async (payload: {
      entertainer_id: string;
      target_id: string;
      strategy_instruction: string;
    }) => (await api.post("/outreach/strategy-update", payload)).data,
    researchRefinement: async (payload: { entertainer_id: string; user_instruction: string }) =>
      (await api.post("/outreach/research-refinement", payload)).data,
    pendingFollowups: async () => (await api.get("/outreach/pending-followup")).data,
  },
  conversations: {
    list: async (entertainerId: string) => (await api.get(`/conversations/list/${entertainerId}`)).data,
    get: async (targetId: string) => (await api.get<Conversation>(`/conversations/${targetId}`)).data,
    getByPitch: async (pitchId: string) => (await api.get<Conversation>(`/conversations/by-pitch/${pitchId}`)).data,
    logReply: async (payload: {
      entertainer_id: string;
      target_id: string;
      reply_body: string;
      reply_sentiment?: string;
    }) => (await api.post("/conversations/reply", payload)).data,
  },
  analytics: {
    summary: async (entertainerId: string) =>
      (await api.get(`/analytics/summary/${entertainerId}`)).data,
    insights: async (entertainerId: string) =>
      (await api.get<Insight[]>(`/analytics/insights/${entertainerId}`)).data,
  },
  bookings: {
    active: async () => (await api.get("/bookings/active")).data,
    completedUnrebooked: async () => (await api.get("/bookings/completed-unrebooked")).data,
    resolvePerformance: async (bookingId: string) =>
      (await api.patch(`/bookings/${bookingId}/resolve-performance`)).data,
    messages: async (bookingId: string) => (await api.get(`/bookings/messages/${bookingId}`)).data,
    markBookingMessageSent: async (messageId: string) =>
      (await api.patch(`/bookings/conversation-message/${messageId}`)).data,
  },
  gmail: {
    status: async (entertainerId: string) =>
      (await api.get("/gmail/status", { params: { entertainer_id: entertainerId } })).data,
    authUrl: async (entertainerId: string, returnTo = "/onboarding?gmail=connected") =>
      (await api.get("/gmail/auth-url", { params: { entertainer_id: entertainerId, return_to: returnTo } })).data,
    sendPitch: async (pitchId: string) =>
      (await api.post(`/gmail/send-pitch/${pitchId}`)).data,
    syncReplies: async (entertainerId: string) =>
      (await api.post("/gmail/sync-replies", null, { params: { entertainer_id: entertainerId } })).data,
  },
  agentEvents: {
    recent: async () => (await api.get<AgentEvent[]>("/agent-events/recent")).data,
    status: async () => (await api.get("/agents/status")).data,
  },
};
