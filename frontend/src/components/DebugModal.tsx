import React, { useEffect, useState } from "react";
import { Terminal, X, RefreshCw, ChevronDown, ChevronRight, Cpu } from "lucide-react";

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

interface DebugModalProps {
  isOpen: boolean;
  sessionId: string;
  onClose: () => void;
}

export const DebugModal: React.FC<DebugModalProps> = ({
  isOpen,
  sessionId,
  onClose,
}) => {
  const [logs, setLogs] = useState<DebugLogItem[]>([]);
  const [activeMemory, setActiveMemory] = useState<Record<string, unknown> | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [expandedLogId, setExpandedLogId] = useState<number | null>(null);

  const fetchDebugData = async () => {
    if (!sessionId) return;
    setIsLoading(true);
    try {
      const res = await fetch(`/api/chat/sessions/${sessionId}/debug`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.debug_logs || []);
        setActiveMemory(data.active_memory || null);
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
      fetchDebugData();
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, sessionId, onClose]);

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
                <span className="px-2 py-0.5 text-[10px] font-bold bg-purple-950 text-purple-300 border border-purple-800 rounded-md">
                  Session: {sessionId.slice(0, 16)}...
                </span>
              </h2>
              <p className="text-[11px] text-slate-400 font-sans">
                Real-time capture of prompts, system instructions, and context payloads passed to LLMs
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchDebugData}
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

        {/* Active Context Memory Summary */}
        {activeMemory && (
          <div className="px-6 py-3 border-b border-slate-800 bg-[#0f1629] text-[11px]">
            <div className="text-purple-400 font-bold mb-1 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" />
              <span>Active SQLite Context Memory:</span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-300">
              <div>
                <span className="text-slate-500">Active Ticker:</span>{" "}
                <span className="text-cyan-300 font-bold">{String(activeMemory.last_ticker || "None")}</span>
              </div>
              <div>
                <span className="text-slate-500">Discovered Candidates:</span>{" "}
                <span className="text-indigo-300">{Array.isArray(activeMemory.last_discovered_tickers) ? activeMemory.last_discovered_tickers.join(", ") : "None"}</span>
              </div>
            </div>
          </div>
        )}

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {isLoading && logs.length === 0 ? (
            <div className="flex items-center justify-center py-16 text-slate-400">
              <div className="w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin mr-2" />
              Loading LLM context trace...
            </div>
          ) : logs.length === 0 ? (
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
                          log.status === "api_success"
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
                          Full Prompt Sent to LLM
                        </div>
                        <pre className="p-2.5 rounded bg-slate-950 border border-slate-800 text-slate-200 overflow-x-auto whitespace-pre-wrap max-h-48 text-[11px]">
                          {log.prompt}
                        </pre>
                      </div>

                      {/* Response */}
                      {log.response && (
                        <div>
                          <div className="text-[10px] uppercase font-bold text-indigo-400 mb-1">
                            LLM Output Response
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
          )}
        </div>
      </div>
    </div>
  );
};
