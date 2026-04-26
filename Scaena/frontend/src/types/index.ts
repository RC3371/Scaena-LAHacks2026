export type AgentId = "agent1" | "agent2" | "agent3" | "agent4" | "system" | "user";
export type AgentStatus = "idle" | "working" | "complete" | "error";

export interface AgentEvent {
  agent_id: AgentId;
  event_type: string;
  message: string;
  entertainer_id?: string;
  target_id?: string;
  conclusion?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface Entertainer {
  id: string;
  name: string;
  type: string;
  genre?: string;
  location?: string;
  experience_years?: number;
  social_followers?: number;
  highlights?: string;
  links?: string;
  current_rate?: number;
  outreach_mode: "manual_approve" | "auto_pitch";
}

export interface Venue {
  id: string;
  entertainer_id: string;
  name: string;
  contact_name?: string;
  contact_email?: string;
  source_url?: string;
  venue_type?: string;
  typical_pay?: string;
  fit_score?: number;
  contact_approach?: string;
  why_fits?: string;
}

export interface Pitch {
  id: string;
  entertainer_id: string;
  venue_name: string;
  entertainer_type?: string;
  recipient_email?: string;
  pitch_subject: string;
  pitch_body: string;
  proposed_rate?: number;
  status: string;
  followup_count: number;
  response_type?: string;
  strategy_note?: string;
  gmail_message_id?: string;
  gmail_thread_id?: string;
  created_at: string;
  sent_at?: string;
}

export interface ConversationMessage {
  id: string;
  direction: "outbound" | "inbound";
  message_type: string;
  subject?: string;
  body: string;
  sentiment?: string;
  gmail_message_id?: string;
  gmail_thread_id?: string;
  from_email?: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  pitch_id: string;
  venue_name: string;
  interest_level?: string;
  signals?: string[] | string;
  what_worked?: string;
  what_to_do_next?: string;
  conversion_likelihood?: number;
  messages: ConversationMessage[];
}

export interface Insight {
  id: string;
  entertainer_id: string;
  round_number: number;
  best_venue_types: string;
  avoid_segments: string;
  best_pitch_angle: string;
  optimal_price: number;
  insights_narrative: string;
  created_at: string;
}
