export type AgentType = "manager" | "research" | "analysis" | "investment" | "security";

export interface AgentStep {
  agent: string;
  message: string;
  timestamp?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  steps?: AgentStep[];
  agent_data?: Record<string, unknown>;
  isStreaming?: boolean;
}

export interface PersonasResponse {
  personas: Record<string, string>;
  defaults: Record<string, string>;
}

export interface HealthStatus {
  status: string;
  app: string;
  version: string;
}

export interface ChatSessionSummary {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_ticker?: string;
  summary?: string;
}

export interface ChatSessionDetail {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: {
    role: "user" | "assistant";
    content: string;
    timestamp: string;
  }[];
  memory?: Record<string, unknown>;
}

export interface SecurityAuditItem {
  control: string;
  status: "PASS" | "FAIL" | "WARN";
  details: string;
}

export interface SecurityAuditReport {
  timestamp: string;
  overall_status: string;
  security_score: number;
  checks_passed: number;
  checks_total: number;
  audit_results: SecurityAuditItem[];
}
