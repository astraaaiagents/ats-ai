/* ── Auth ─────────────────────────────────────────────────────────── */

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

/* ── User ─────────────────────────────────────────────────────────── */

export interface UserResponse {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/* ── Candidate ────────────────────────────────────────────────────── */

export interface CandidateSkillResponse {
  id: string;
  skill_name: string;
  proficiency: number | null;
  years_experience: number | null;
}

export interface CandidateDocumentResponse {
  id: string;
  document_type: string;
  file_name: string;
  file_size_bytes: number;
  s3_key: string;
  created_at: string;
}

export interface CandidateTimelineEvent {
  id: string;
  event_type: string;
  description: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface CandidateResponse {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  current_title: string | null;
  current_employer: string | null;
  location: string | null;
  salary_expectation_min: number | null;
  salary_expectation_max: number | null;
  visa_status: string | null;
  notice_period_days: number | null;
  source: string | null;
  status: string;
  owner_id: string | null;
  ai_summary: string | null;
  ai_summary_generated_at: string | null;
  is_ai_summary_edited: boolean;
  skills: CandidateSkillResponse[];
  documents: CandidateDocumentResponse[];
  timeline: CandidateTimelineEvent[];
  created_at: string;
  updated_at: string;
}

export interface CandidateStatusUpdate {
  status: string;
  reason?: string | null;
}

export interface PaginationInfo {
  next_cursor: string | null;
  has_more: boolean;
  total: number;
  sort: string | null;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
}

/* ── Agent / Conversation ─────────────────────────────────────────── */

export interface AgentMessageResponse {
  id: string;
  role: "agent" | "user" | "system";
  content: string;
  cards: Record<string, unknown>[];
  actions: AgentActionResponse[];
  sources: SourceRefResponse[];
  confidence: number | null;
  is_proactive: boolean;
  created_at: string;
}

export interface AgentActionResponse {
  id: string;
  label: string;
  type: "approve" | "reject" | "submit" | "edit_preference" | "schedule_interview" | "draft_outreach";
  payload: Record<string, unknown>;
  confirmation: string | null;
}

export interface SourceRefResponse {
  type: "internal_db" | "job_board" | "sub_vendor" | "client_portal";
  identifier: string;
  timestamp: string;
}

export interface ConversationHistoryResponse {
  session_id: string;
  title: string | null;
  messages: AgentMessageResponse[];
}

export interface ConversationRequest {
  message: string;
  session_id?: string | null;
}

/* ── Preferences ──────────────────────────────────────────────────── */

export interface PreferenceResponse {
  explicit: Record<string, unknown>;
  implicit_scores: Record<string, number>;
  last_updated: string;
}

export interface PreferenceUpdate {
  explicit: Record<string, unknown>;
}

/* ── Proactive Alerts ─────────────────────────────────────────────── */

export interface ProactiveAlertResponse {
  id: string;
  alert_type: "new_match" | "pipeline_update" | "feedback_reminder" | "weekly_digest";
  title: string;
  body: string;
  data: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}

export interface ProactiveAlertsResponse {
  alerts: ProactiveAlertResponse[];
}

/* ── Action Log ───────────────────────────────────────────────────── */

export interface ActionLogEntry {
  id: string;
  action_type: string;
  agent_name: string;
  input_pseudonymized: string;
  output_pseudonymized: string;
  created_at: string;
}

/* ── SSE Event Types ──────────────────────────────────────────────── */

export interface SSEMessageStart {
  session_id: string;
  timestamp: string;
}

export interface SSEContent {
  type: "text";
  content: string;
}

export interface SSECard {
  type: "candidate" | "job" | "alert" | "summary" | "preference";
  data: Record<string, unknown>;
  fitScore?: number;
}

export interface SSEAction {
  id: string;
  label: string;
  type: string;
  payload: Record<string, unknown>;
}

export interface SSEMessageEnd {
  confidence: number;
  sources: SourceRefResponse[];
  message_id: string;
}

export type SSEEvent = SSEMessageStart | SSEContent | SSECard | SSEAction | SSEMessageEnd;

/* ── Pipeline ─────────────────────────────────────────────────────── */

export const PIPELINE_STAGES = ["sourced", "reviewing", "submitted", "interviewing", "placed"] as const;
export type PipelineStage = (typeof PIPELINE_STAGES)[number];

/* ── Feed ─────────────────────────────────────────────────────────── */

export type FeedItemType = "agent" | "user" | "system" | "alert";

export interface FeedItem {
  id: string;
  type: FeedItemType;
  content: string;
  badge?: string;
  cards?: Record<string, unknown>[];
  actions?: AgentActionResponse[];
  created_at: string;
}

/* ── Job (mock — no backend model) ────────────────────────────────── */

export interface Job {
  id: string;
  req_id: string;
  client_name: string;
  role_title: string;
  location: string;
  status: "healthy" | "needs_attention" | "on_track" | "critical";
  domains: string[];
  candidate_count: number;
  pipeline_summary: string;
  agent_insight: string;
}

/* ── Error ────────────────────────────────────────────────────────── */

export interface ErrorDetail {
  code: string;
  message: string;
  details: Array<{ field: string; reason: string; code: string }>;
}

export interface ErrorResponse {
  error: ErrorDetail;
}
