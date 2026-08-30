import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from './components/Header';
import { ChatInterface } from './components/ChatInterface';
import { PersonaModal } from './components/PersonaModal';
import type { ChatMessage, HealthStatus, AgentStep } from './types';
import { fetchHealth, streamChat, sendChatFallback } from './services/api';

export const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>(() => `sess_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPersonasOpen, setIsPersonasOpen] = useState<boolean>(false);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState<boolean>(true);

  const abortControllerRef = useRef<AbortController | null>(null);

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

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  const handleNewSession = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    const newId = `sess_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
    setSessionId(newId);
    setMessages([]);
    setInput('');
    setIsLoading(false);
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

    setInput('');
    const userMsgId = `user_${Date.now()}`;
    const assistantMsgId = `asst_${Date.now()}`;
    const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const userMessage: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: promptToSend,
      timestamp: timeStr,
    };

    const initialAssistantMessage: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: timeStr,
      steps: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let receivedAnyStreamData = false;
    let accumulatedContent = '';
    const accumulatedSteps: AgentStep[] = [];

    try {
      await streamChat(
        promptToSend,
        sessionId,
        {
          onStep: (step) => {
            receivedAnyStreamData = true;
            accumulatedSteps.push(step);
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, steps: [...accumulatedSteps] }
                  : m
              )
            );
          },
          onChunk: (chunk) => {
            receivedAnyStreamData = true;
            accumulatedContent += chunk;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: accumulatedContent }
                  : m
              )
            );
          },
          onDone: (data) => {
            receivedAnyStreamData = true;
            if (data.session_id) {
              setSessionId(data.session_id);
            }
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? {
                      ...m,
                      content: data.response || accumulatedContent,
                      steps: accumulatedSteps,
                      agent_data: data.agent_data,
                      isStreaming: false,
                    }
                  : m
              )
            );
          },
          onError: (err) => {
            throw err;
          },
        },
        controller.signal
      );
    } catch (err) {
      if (controller.signal.aborted) {
        return;
      }

      // If SSE streaming failed before delivering data, attempt fallback endpoint
      if (!receivedAnyStreamData) {
        try {
          const fallbackData = await sendChatFallback(promptToSend, sessionId);
          if (fallbackData.session_id) {
            setSessionId(fallbackData.session_id);
          }
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    content: fallbackData.response,
                    steps: fallbackData.steps || [],
                    agent_data: fallbackData.agent_data,
                    isStreaming: false,
                  }
                : m
            )
          );
        } catch (fallbackErr) {
          const errMsg = fallbackErr instanceof Error ? fallbackErr.message : String(fallbackErr);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsgId
                ? {
                    ...m,
                    content: `Error: Unable to complete request. ${errMsg}`,
                    isStreaming: false,
                  }
                : m
            )
          );
        }
      } else {
        const streamErrMsg = err instanceof Error ? err.message : String(err);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: accumulatedContent
                    ? `${accumulatedContent}\n\n[Stream disconnected: ${streamErrMsg}]`
                    : `Error: ${streamErrMsg}`,
                  isStreaming: false,
                }
              : m
          )
        );
      }
    } finally {
      abortControllerRef.current = null;
      setIsLoading(false);
      setMessages((prev) =>
        prev.map((m) => (m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
      );
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#090d16] text-slate-100 overflow-hidden select-text">
      {/* Header */}
      <Header
        health={health}
        isHealthLoading={isHealthLoading}
        onNewSession={handleNewSession}
        onOpenPersonas={() => setIsPersonasOpen(true)}
      />

      {/* Main Chat Interface */}
      <main className="flex-1 flex flex-col min-h-0 relative">
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

      {/* Personas Modal */}
      <PersonaModal
        isOpen={isPersonasOpen}
        onClose={() => setIsPersonasOpen(false)}
      />
    </div>
  );
};

export default App;
