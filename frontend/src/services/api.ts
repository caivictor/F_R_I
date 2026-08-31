import type { AgentStep, HealthStatus, PersonasResponse, ChatSessionSummary, ChatSessionDetail } from "../types";

const API_BASE = "";

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/api/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

export async function fetchPersonas(): Promise<PersonasResponse> {
  const res = await fetch(`${API_BASE}/api/personas`);
  if (!res.ok) {
    throw new Error(`Failed to fetch personas: ${res.status}`);
  }
  return res.json();
}

export async function updatePersona(agent: string, persona: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/api/personas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent, persona }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to update persona: ${res.status}`);
  }
  return res.json();
}

export async function resetPersona(agent?: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/api/personas/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent: agent || null }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to reset persona: ${res.status}`);
  }
  return res.json();
}

export async function fetchSessions(): Promise<ChatSessionSummary[]> {
  const res = await fetch(`${API_BASE}/api/chat/sessions`);
  if (!res.ok) {
    throw new Error(`Failed to fetch sessions: ${res.status}`);
  }
  return res.json();
}

export async function fetchSessionDetails(sessionId: string): Promise<ChatSessionDetail> {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch session ${sessionId}: ${res.status}`);
  }
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<Record<string, unknown>> {
  const res = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Failed to delete session: ${res.status}`);
  }
  return res.json();
}



export interface StreamChatCallbacks {
  onStep?: (step: AgentStep) => void;
  onChunk?: (chunk: string) => void;
  onDone?: (data: { response: string; session_id: string; agent_data?: Record<string, unknown> }) => void;
  onError?: (error: Error) => void;
}

export async function streamChat(
  message: string,
  sessionId?: string,
  callbacks?: StreamChatCallbacks,
  signal?: AbortSignal
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ message, session_id: sessionId || null }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => "");
      throw new Error(`Server returned ${response.status}: ${errorText || response.statusText}`);
    }

    if (!response.body) {
      throw new Error("Response body is null");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;

        let jsonStr = trimmed;
        if (trimmed.startsWith("data: ")) {
          jsonStr = trimmed.slice(6).trim();
        }

        if (jsonStr === "[DONE]") continue;

        try {
          const parsed = JSON.parse(jsonStr);
          if (parsed.type === "step") {
            callbacks?.onStep?.({
              agent: parsed.agent,
              message: parsed.message,
              timestamp: new Date().toLocaleTimeString(),
            });
          } else if (parsed.type === "chunk") {
            callbacks?.onChunk?.(parsed.content);
          } else if (parsed.type === "done") {
            callbacks?.onDone?.({
              response: parsed.response,
              session_id: parsed.session_id,
              agent_data: parsed.agent_data,
            });
          } else if (parsed.type === "error") {
            callbacks?.onError?.(new Error(parsed.message || "Stream error occurred"));
          }
        } catch {
          // Ignore partial or unparseable SSE line fragments
        }
      }
    }
  } catch (err) {
    if (signal?.aborted) {
      return;
    }
    callbacks?.onError?.(err instanceof Error ? err : new Error(String(err)));
  }
}

export async function sendChatFallback(
  message: string,
  sessionId?: string
): Promise<{
  response: string;
  session_id: string;
  steps: AgentStep[];
  agent_data: Record<string, unknown>;
}> {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId || null }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Chat request failed: ${res.status}`);
  }

  return res.json();
}
