export type AgentType = 'manager' | 'research' | 'analysis' | 'investment';

export interface AgentStep {
  agent: string;
  message: string;
  timestamp?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
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
