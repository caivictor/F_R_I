import React from "react";
import { Clock, MessageSquare, Trash2, X, ArrowRight, Sparkles } from "lucide-react";
import type { ChatSessionSummary } from "../types";

interface SessionsModalProps {
  isOpen: boolean;
  sessions: ChatSessionSummary[];
  currentSessionId: string;
  isLoading: boolean;
  onClose: () => void;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onNewSession: () => void;
}

export const SessionsModal: React.FC<SessionsModalProps> = ({
  isOpen,
  sessions,
  currentSessionId,
  isLoading,
  onClose,
  onSelectSession,
  onDeleteSession,
  onNewSession,
}) => {
    React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-[#0f172a] border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0c1222]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-cyan-950/80 border border-cyan-800/60 text-cyan-400">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 font-mono tracking-wide">
                Chat History & Context Memory
              </h2>
              <p className="text-xs text-slate-400">
                Persistent sessions saved in SQLite with long-context continuity
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action toolbar */}
        <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-900/50 flex items-center justify-between">
          <span className="text-xs text-slate-400 font-mono">
            {sessions.length} {sessions.length === 1 ? "Session" : "Sessions"} Persisted
          </span>
          <button
            onClick={() => {
              onNewSession();
              onClose();
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-cyan-400 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/60 rounded-lg transition-colors cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New Chat Thread</span>
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-slate-400 text-sm">
              <div className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mr-2" />
              Loading persistent sessions...
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-12">
              <MessageSquare className="w-12 h-12 text-slate-600 mx-auto mb-3" />
              <p className="text-slate-300 text-sm font-medium">No past sessions found</p>
              <p className="text-slate-500 text-xs mt-1">
                Start chatting to establish continuous conversational memory
              </p>
            </div>
          ) : (
            sessions.map((sess) => {
              const isCurrent = sess.session_id === currentSessionId;
              return (
                <div
                  key={sess.session_id}
                  className={`p-4 rounded-xl border transition-all flex items-center justify-between gap-4 group ${
                    isCurrent
                      ? "bg-slate-800/90 border-cyan-500/60 shadow-lg shadow-cyan-950/20"
                      : "bg-slate-900/60 hover:bg-slate-800/60 border-slate-800 hover:border-slate-700"
                  }`}
                >
                  <div
                    onClick={() => {
                      onSelectSession(sess.session_id);
                      onClose();
                    }}
                    className="flex-1 min-w-0 cursor-pointer"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-slate-200 truncate font-mono">
                        {sess.title || "Conversation"}
                      </span>
                      {isCurrent && (
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase bg-cyan-900/80 text-cyan-300 border border-cyan-700/60 rounded-full">
                          Active
                        </span>
                      )}
                      {sess.last_ticker && (
                        <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-indigo-950 text-indigo-300 border border-indigo-800 rounded-md">
                          ${sess.last_ticker}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                      <span>{sess.message_count} messages</span>
                      <span>•</span>
                      <span>{sess.updated_at}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        onSelectSession(sess.session_id);
                        onClose();
                      }}
                      className="p-2 text-cyan-400 hover:bg-cyan-950/80 rounded-lg transition-colors cursor-pointer"
                      title="Open and resume session"
                    >
                      <ArrowRight className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(sess.session_id);
                      }}
                      className="p-2 text-slate-500 hover:text-rose-400 hover:bg-rose-950/40 rounded-lg transition-colors cursor-pointer"
                      title="Delete session"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
