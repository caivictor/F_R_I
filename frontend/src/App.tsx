import React, { useState, useEffect, useRef, useCallback } from "react";
import { Header } from "./components/Header";
import { ChatInterface } from "./components/ChatInterface";
import { PersonaModal } from "./components/PersonaModal";
import { SessionsModal } from "./components/SessionsModal";
import { SecurityModal } from "./components/SecurityModal";
import { DebugModal } from "./components/DebugModal";
import type { ChatMessage, HealthStatus, AgentStep, ChatSessionSummary, SecurityAuditReport } from "./types";
import { fetchHealth, streamChat, sendChatFallback, fetchSessions, fetchSessionDetails, deleteSession, fetchSecurityAudit } from "./services/api";

const ACTIVE_SESSION_STORAGE_KEY = "fri_active_session_id";

export const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>(() => {
    return localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY) || `sess_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPersonasOpen, setIsPersonasOpen] = useState<boolean>(false);
  const [isSessionsOpen, setIsSessionsOpen] = useState<boolean>(false);
  const [isSecurityOpen, setIsSecurityOpen] = useState<boolean>(false);
  const [isDebugOpen, setIsDebugOpen] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState<boolean>(true);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [isSessionsLoading, setIsSessionsLoading] = useState<boolean>(false);
  const [securityReport, setSecurityReport] = useState<SecurityAuditReport | null>(null);
  const [isSecurityLoading, setIsSecurityLoading] = useState<boolean>(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Sync active session ID to localStorage
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, sessionId);
    }
  }, [sessionId]);

  const checkHealth = useCallback(async () => {
    try {
      setIsHealthLoading(true);
      const data = await fetchHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setIsHealthLoading(false);
    }
  }, []);

  const loadSessionsList = useCallback(async () => {
    try {
      setIsSessionsLoading(true);
      const list = await fetchSessions();
      setSessions(list);
    } catch {
      // Ignore
    } finally {
      setIsSessionsLoading(false);
    }
  }, []);

  const loadSecurityAudit = useCallback(async () => {
    try {
      setIsSecurityLoading(true);
      const rep = await fetchSecurityAudit();
      setSecurityReport(rep);
    } catch {
      // Ignore
    } finally {
      setIsSecurityLoading(false);
    }
  }, []);

  // Restore existing session messages on mount if available
  useEffect(() => {
    checkHealth();
    loadSessionsList();

    const restoreInitialSession = async () => {
      const savedId = localStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
      if (savedId) {
        try {
          const details = await fetchSessionDetails(savedId);
          if (details && details.messages && details.messages.length > 0) {
            const formatted: ChatMessage[] = details.messages.map((m, idx) => ({
              id: `msg_${idx}_${Date.now()}`,
              role: m.role,
              content: m.content,
              timestamp: m.timestamp,
            }));
            setMessages(formatted);
          }
        } catch {
          // New session fallback
        }
      }
    };

    restoreInitialSession();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth, loadSessionsList]);

  const handleNewSession = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    const newId = `sess_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    setSessionId(newId);
    localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, newId);
    setMessages([]);
    setInput("");
    setIsLoading(false);
  };

  const handleSelectSession = async (targetSessionId: string) => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(true);
    try {
      const details = await fetchSessionDetails(targetSessionId);
      setSessionId(details.session_id);
      localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, details.session_id);
      const formattedMessages: ChatMessage[] = (details.messages || []).map((m, idx) => ({
        id: `msg_${idx}_${Date.now()}`,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp,
      }));
      setMessages(formattedMessages);
    } catch {
      // Ignore
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSession = async (targetSessionId: string) => {
    try {
      await deleteSession(targetSessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== targetSessionId));
      if (sessionId === targetSessionId) {
        handleNewSession();
      }
    } catch {
      // Ignore
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setMessages((prev) =>
      prev.map((msg) => (msg.isStreaming ? { ...msg, isStreaming: false } : msg))
    );
  };

  const handleSendMessage = async (customPrompt?: string) => {
    const promptToSend = (customPrompt !== undefined ? customPrompt : input).trim();
    if (!promptToSend || isLoading) return;

    setInput("");
    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;
    const timeStr = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });

    const userMessage: ChatMessage = {
      id: userMsgId,
      role: "user",
      content: promptToSend,
      timestamp: timeStr,
    };

    const initialAssistantMessage: ChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      timestamp: timeStr,
      steps: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsLoading(true);

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    let streamedAny = false;

    try {
      await streamChat(
        promptToSend,
        sessionId,
        {
          onStep: (step: AgentStep) => {
            streamedAny = true;
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === assistantMsgId) {
                  const existingSteps = msg.steps || [];
                  return {
                    ...msg,
                    steps: [...existingSteps, step],
                  };
                }
                return msg;
              })
            );
          },
          onChunk: (chunk: string) => {
            streamedAny = true;
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === assistantMsgId) {
                  return {
                    ...msg,
                    content: msg.content + chunk,
                  };
                }
                return msg;
              })
            );
          },
          onDone: (data) => {
            setSessionId(data.session_id);
            localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, data.session_id);
            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === assistantMsgId) {
                  return {
                    ...msg,
                    content: data.response,
                    agent_data: data.agent_data,
                    isStreaming: false,
                  };
                }
                return msg;
              })
            );
            loadSessionsList();
          },
          onError: async (error: Error) => {
            if (!streamedAny && !abortController.signal.aborted) {
              try {
                const fallbackData = await sendChatFallback(promptToSend, sessionId);
                setSessionId(fallbackData.session_id);
                localStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, fallbackData.session_id);
                setMessages((prev) =>
                  prev.map((msg) => {
                    if (msg.id === assistantMsgId) {
                      return {
                        ...msg,
                        content: fallbackData.response,
                        steps: fallbackData.steps,
                        agent_data: fallbackData.agent_data,
                        isStreaming: false,
                      };
                    }
                    return msg;
                  })
                );
                loadSessionsList();
                return;
              } catch {
                // Ignore fallback error
              }
            }

            setMessages((prev) =>
              prev.map((msg) => {
                if (msg.id === assistantMsgId) {
                  return {
                    ...msg,
                    content:
                      msg.content ||
                      `**Error:** Unable to complete request (${error.message}). Please verify the server connection.`,
                    isStreaming: false,
                  };
                }
                return msg;
              })
            );
          },
        },
        abortController.signal
      );
    } catch {
      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === assistantMsgId) {
            return {
              ...msg,
              content: msg.content || "**Error:** Failed to connect to F.R.I. assistant.",
              isStreaming: false,
            };
          }
          return msg;
        })
      );
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#070b14] text-slate-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Header */}
      <Header
        health={health}
        isHealthLoading={isHealthLoading}
        onNewSession={handleNewSession}
        onOpenPersonas={() => setIsPersonasOpen(true)}
        onOpenSessions={() => {
          loadSessionsList();
          setIsSessionsOpen(true);
        }}
        onOpenSecurity={() => {
          loadSecurityAudit();
          setIsSecurityOpen(true);
        }}
        onOpenDebug={() => setIsDebugOpen(true)}
      />

      {/* Main Chat Interface */}
      <main className="flex-1 overflow-hidden relative flex flex-col">
        <ChatInterface
          messages={messages}
          sessionId={sessionId}
          input={input}
          setInput={setInput}
          onSubmit={handleSendMessage}
          onStop={handleStop}
          isLoading={isLoading}
        />
      </main>

      {/* Personas Configuration Modal */}
      <PersonaModal
        isOpen={isPersonasOpen}
        onClose={() => setIsPersonasOpen(false)}
      />

      {/* Chat History & Sessions Modal */}
      <SessionsModal
        isOpen={isSessionsOpen}
        sessions={sessions}
        currentSessionId={sessionId}
        isLoading={isSessionsLoading}
        onClose={() => setIsSessionsOpen(false)}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onNewSession={handleNewSession}
      />

      {/* Security Agent Posture Modal */}
      <SecurityModal
        isOpen={isSecurityOpen}
        auditReport={securityReport}
        isLoading={isSecurityLoading}
        onClose={() => setIsSecurityOpen(false)}
        onRefresh={loadSecurityAudit}
      />

      {/* LLM Context & Debug Inspector Modal */}
      <DebugModal
        isOpen={isDebugOpen}
        sessionId={sessionId}
        sessions={sessions}
        onClose={() => setIsDebugOpen(false)}
        onSelectSession={handleSelectSession}
      />
    </div>
  );
};

export default App;
