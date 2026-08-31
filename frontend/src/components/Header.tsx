import React from "react";
import { Activity, Bot, PlusCircle, Server, Clock, ShieldCheck } from "lucide-react";
import type { HealthStatus } from "../types";

interface HeaderProps {
  health: HealthStatus | null;
  isHealthLoading: boolean;
  onNewSession: () => void;
  onOpenPersonas: () => void;
  onOpenSessions: () => void;
  onOpenSecurity: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  isHealthLoading,
  onNewSession,
  onOpenPersonas,
  onOpenSessions,
  onOpenSecurity,
}) => {
  const isHealthy = health?.status === "ok";

  return (
    <header className="border-b border-slate-800 bg-[#0c1222]/90 backdrop-blur sticky top-0 z-30 px-4 lg:px-8 py-3 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Logo and App Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-500 to-purple-600 p-[2px] shadow-lg shadow-indigo-500/20">
            <div className="w-full h-full bg-[#0b0f19] rounded-[10px] flex items-center justify-center">
              <Activity className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-wider text-slate-100 uppercase font-mono">
                F.R.I.
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wide uppercase bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 rounded-full">
                Multi-Agent AI
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Financial Research &amp; Investment Companion
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          {/* Health Status Indicator */}
          <div
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300 shadow-inner"
            title={isHealthy ? `Backend Connected (${health?.app} v${health?.version})` : "Backend Unreachable"}
          >
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  isHealthLoading
                    ? "bg-amber-400 animate-pulse"
                    : isHealthy
                    ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]"
                    : "bg-rose-500"
                }`}
              />
              <span className="text-[11px] font-mono text-slate-300">
                {isHealthLoading
                  ? "Connecting..."
                  : isHealthy
                  ? `v${health?.version || "1.1.0"}`
                  : "Offline"}
              </span>
            </div>
          </div>

          {/* History / Sessions Button */}
          <button
            onClick={onOpenSessions}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all shadow-sm active:scale-95 cursor-pointer"
            title="Chat History & Sessions"
          >
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden md:inline">History</span>
          </button>

          {/* Security Posture Audit Button */}
          <button
            onClick={onOpenSecurity}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all shadow-sm active:scale-95 cursor-pointer"
            title="Security Agent Audit & Guardrails"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span className="hidden md:inline">Security</span>
          </button>

          {/* Agent Personas Button */}
          <button
            onClick={onOpenPersonas}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition-all shadow-sm active:scale-95 cursor-pointer"
            title="Configure Agent Personas"
          >
            <Bot className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden md:inline">Personas</span>
          </button>

          {/* New Session Button */}
          <button
            onClick={onNewSession}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-medium shadow-md shadow-cyan-900/30 transition-all active:scale-95 cursor-pointer"
            title="Start a new chat session"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>
        </div>
      </div>
    </header>
  );
};
