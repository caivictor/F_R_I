import React, { useEffect, useState } from "react";
import { Terminal, X, RefreshCw, ChevronDown, ChevronRight, MessageSquare, CheckCircle2 } from "lucide-react";
import type { ChatSessionSummary } from "../types";

interface DebugLogItem {
  id: number;
  session_id: string;
  timestamp: string;
  agent: string;
  model: string;
  system_instruction?: string;
  prompt: string;
  context_data?: Record<string, unknown>;
  response?: string;
  latency_ms: number;
  status: string;
}

interface MessageItem {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

interface DebugModalProps {
  isOpen: boolean;
  sessionId: string;
  sessions?: ChatSessionSummary[];
  onClose: () => void;
  onSelectSession?: (id: string) => void;
}

export const DebugModal: React.FC<DebugModalProps> = ({
  isOpen,
  sessionId,
  sessions = [],
  onClose,
  onSelectSession,
}) => {
  const [selectedSessionId, setSelectedSessionId] = useState<string>(sessionId);
  const [activeTab, setActiveTab] = useState<"logs" | "conversation" | "memory">("logs");
  const [logs, setLogs] = useState<DebugLogItem[]>([]);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [activeMemory, setActiveMemory] = useState<Record<string, unknown> | null>(null);
  const [sessionTitle, setSessionTitle] = useState<string>("Active Session");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);

  useEffect(() => {
    if (sessionId) {
      setSelectedSessionId(sessionId);
    }
  }, [sessionId]);

  const fetchDebugData = async (targetId: string) => {
    if (!targetId) return;
    setIsLoading(true);
    try {
      const res = await fetch(`/api/chat/sessions/${targetId}/debug`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.debug_logs || []);
        setMessages(data.messages || []);
        setActiveMemory(data.active_memory || null);
        setSessionTitle(data.session_title || "Active Session");
        if (data.debug_logs && data.debug_logs.length > 0 && expandedLogId === null) {
          setExpandedLogId(data.debug_logs[data.debug_logs.length - 1].id);
        }
      }
    } catch {
      // Ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      fetchDebugData(selectedSessionId);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, selectedSessionId, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0b101d] border border-slate-700 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-mono text-xs">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#090d18]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-950/80 border border-purple-800/60 text-purple-400">
              <Terminal className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 tracking-wide flex items-center gap-2">
                LLM Context &amp; Debug Inspector
              </h2>
              <p className="text-[11px] text-slate-400 font-sans">
                Real-time capture of prompts, system instructions, and context payloads passed to LLMs
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchDebugData(selectedSessionId)}
              disabled={isLoading}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
              title="Refresh debug logs"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin" : ""}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Toolbar with Session Selector and Tabs */}
        <div className="px-6 py-2.5 border-b border-slate-800 bg-[#0d1424] flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400 font-sans font-medium">Session:</span>
            <select
              value={selectedSessionId}
              onChange={(e) => {
                const newId = e.target.value;
                setSelectedSessionId(newId);
                if (onSelectSession) onSelectSession(newId);
                fetchDebugData(newId);
              }}
              className="bg-slate-900 border border-slate-700 text-slate-200 text-[11px] rounded-lg px-2.5 py-1 focus:outline-none focus:border-purple-500 font-mono"
            >
              <option value={selectedSessionId}>Current: {sessionTitle} ({selectedSessionId.slice(0, 8)}...)</option>
              {sessions
                .filter((s) => s.session_id !== selectedSessionId)
                .map((s) => (
                  <option key={s.session_id} value={s.session_id}>
                    {s.title} ({s.session_id.slice(0, 8)}...)
                  </option>
                ))}
            </select>
          </div>

          <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveTab("logs")}
              className={`px-3 py-1 rounded-md text-[11px] font-sans font-medium transition-all ${
                activeTab === "logs"
                  ? "bg-purple-950 text-purple-300 border border-purple-800/80 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Context &amp; Prompts ({logs.length})
            </button>
            <button
              onClick={() => setActiveTab("conversation")}
              className={`px-3 py-1 rounded-md text-[11px] font-sans font-medium transition-all ${
                activeTab === "conversation"
                  ? "bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Conversation ({messages.length})
            </button>
            <button
              onClick={() => setActiveTab("memory")}
              className={`px-3 py-1 rounded-md text-[11px] font-sans font-medium transition-all ${
                activeTab === "memory"
                  ? "bg-emerald-950 text-emerald-300 border border-emerald-800/80 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              Active Memory
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {isLoading && logs.length === 0 && messages.length === 0 ? (
            <div className="flex items-center justify-center py-16 text-slate-400">
              <div className="w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin mr-2" />
              Loading debug trace for session...
            </div>
          ) : activeTab === "logs" ? (
            logs.length === 0 ? (
              <div className="text-center py-16 text-slate-500">
                <Terminal className="w-10 h-10 mx-auto mb-2 text-slate-600" />
                <p className="text-slate-300 font-sans font-medium">No LLM interactions logged yet for this session.</p>
                <p className="text-slate-500 text-[11px] font-sans mt-1">
                  Send a message in the chat to see the exact prompt and context payload passed to the AI.
                </p>
              </div>
            ) : (
              logs.map((log) => {
                const isExpanded = expandedLogId === log.id;
                return (
                  <div
                    key={log.id}
                    className="rounded-xl border border-slate-800 bg-slate-900/80 overflow-hidden shadow-sm"
                  >
                    {/* Item Header */}
                    <div
                      onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                      className="px-4 py-3 bg-[#0d1322] hover:bg-[#11192e] flex items-center justify-between cursor-pointer border-b border-slate-800/80 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-purple-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-slate-500" />
                        )}
                        <span className="font-bold text-slate-200 uppercase">
                          [{log.agent}]
                        </span>
                        <span className="text-slate-400 text-[10px]">
                          {log.timestamp}
                        </span>
                        <span className="px-2 py-0.5 text-[9px] rounded bg-slate-800 text-slate-300">
                          {log.model}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-slate-400">
                          {log.latency_ms}ms
                        </span>
                        <span
                          className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase ${
                            log.status === "api_success" || log.status === "turn_completed"
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : "bg-slate-800 text-slate-300 border border-slate-700"
                          }`}
                        >
                          {log.status}
                        </span>
                      </div>
                    </div>

                    {/* Expanded Detail */}
                    {isExpanded && (
                      <div className="p-4 space-y-3 bg-[#080d1a]">
                        {/* Context Data */}
                        {log.context_data && (
                          <div>
                            <div className="text-[10px] uppercase font-bold text-purple-400 mb-1">
                              Injected Context Data
                            </div>
                            <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-emerald-300 overflow-x-auto whitespace-pre-wrap max-h-48 text-[11px]">
                              {JSON.stringify(log.context_data, null, 2)}
                            </pre>
                          </div>
                        )}

                        {/* Prompt */}
                        <div>
                          <div className="text-[10px] uppercase font-bold text-cyan-400 mb-1">
                            Prompt / Instruction Sent to AI
                          </div>
                          <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-200 overflow-x-auto whitespace-pre-wrap max-h-48 text-[11px]">
                            {log.prompt}
                          </pre>
                        </div>

                        {/* Response */}
                        {log.response && (
                          <div>
                            <div className="text-[10px] uppercase font-bold text-indigo-400 mb-1">
                              AI Output Response
                            </div>
                            <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-48 text-[11px]">
                              {log.response}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )
          ) : activeTab === "conversation" ? (
            messages.length === 0 ? (
              <div className="text-center py-16 text-slate-500">
                <MessageSquare className="w-10 h-10 mx-auto mb-2 text-slate-600" />
                <p className="text-slate-300 font-sans font-medium">No messages recorded in this session yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {messages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-xl border ${
                      m.role === "user"
                        ? "bg-slate-900/90 border-cyan-900/60 ml-8"
                        : "bg-[#090e1c] border-slate-800 mr-8"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5 text-[10px] text-slate-500 font-sans">
                      <span className="font-bold uppercase tracking-wider text-slate-300">
                        {m.role === "user" ? "User" : "F.R.I. Manager"}
                      </span>
                      <span>{m.timestamp}</span>
                    </div>
                    <div className="text-slate-200 text-[11px] whitespace-pre-wrap font-sans">
                      {m.content}
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : (
            /* Active Memory Tab */
            <div className="space-y-4">
              <div className="p-4 rounded-xl border border-slate-800 bg-[#090d19]">
                <div className="text-xs uppercase font-bold text-emerald-400 mb-3 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Persistent Context State</span>
                </div>
                <div className="space-y-2 text-slate-300 text-[11px]">
                  <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-500">Session ID:</span>
                    <span className="font-mono text-cyan-300">{selectedSessionId}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-500">Active Ticker Focus:</span>
                    <span className="font-bold text-indigo-300">{String(activeMemory?.last_ticker || "None")}</span>
                  </div>
                  <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                    <span className="text-slate-500">Discovered Candidates:</span>
                    <span className="text-slate-200">
                      {Array.isArray(activeMemory?.last_discovered_tickers)
                        ? activeMemory.last_discovered_tickers.join(", ")
                        : "None"}
                    </span>
                  </div>
                  <div className="pt-2">
                    <span className="text-slate-500 block mb-1">Compressed Context Summary:</span>
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 whitespace-pre-wrap">
                      {String(activeMemory?.summary || "No compressed summary generated yet (conversation is within active window).")}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
