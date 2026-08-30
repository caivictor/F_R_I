import React from 'react';
import { Bot, TrendingUp, Search, PieChart, ShieldCheck, Loader2 } from 'lucide-react';
import type { AgentStep } from '../types';

interface StepProgressProps {
  steps: AgentStep[];
  isStreaming?: boolean;
}

const AGENT_CONFIGS: Record<
  string,
  { label: string; color: string; border: string; bg: string; icon: React.ComponentType<{ className?: string }> }
> = {
  manager: {
    label: 'Manager',
    color: 'text-indigo-400',
    border: 'border-indigo-800/60',
    bg: 'bg-indigo-950/40',
    icon: ShieldCheck,
  },
  research: {
    label: 'Research Agent',
    color: 'text-emerald-400',
    border: 'border-emerald-800/60',
    bg: 'bg-emerald-950/40',
    icon: Search,
  },
  analysis: {
    label: 'Analysis Agent',
    color: 'text-amber-400',
    border: 'border-amber-800/60',
    bg: 'bg-amber-950/40',
    icon: TrendingUp,
  },
  investment: {
    label: 'Investment Agent',
    color: 'text-cyan-400',
    border: 'border-cyan-800/60',
    bg: 'bg-cyan-950/40',
    icon: PieChart,
  },
};

export const StepProgress: React.FC<StepProgressProps> = ({ steps, isStreaming }) => {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="mb-4 rounded-xl bg-slate-900/80 border border-slate-800 p-3 text-xs shadow-inner">
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800/80 text-slate-400 font-mono text-[11px] uppercase tracking-wider">
        <span className="flex items-center gap-1.5">
          <Bot className="w-3.5 h-3.5 text-cyan-400" />
          Multi-Agent Pipeline Trace
        </span>
        <span>{steps.length} {steps.length === 1 ? 'step' : 'steps'}</span>
      </div>

      <div className="space-y-2">
        {steps.map((step, idx) => {
          const config = AGENT_CONFIGS[step.agent.toLowerCase()] || {
            label: step.agent,
            color: 'text-slate-300',
            border: 'border-slate-700',
            bg: 'bg-slate-800/40',
            icon: Bot,
          };
          const Icon = config.icon;
          const isLatest = idx === steps.length - 1;

          return (
            <div
              key={idx}
              className={`flex items-start gap-2.5 p-2 rounded-lg border ${config.bg} ${config.border} transition-all`}
            >
              <div className="mt-0.5 flex-shrink-0">
                {isStreaming && isLatest ? (
                  <Loader2 className={`w-3.5 h-3.5 animate-spin ${config.color}`} />
                ) : (
                  <Icon className={`w-3.5 h-3.5 ${config.color}`} />
                )}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`font-semibold tracking-wide font-mono text-[11px] ${config.color}`}>
                    [{config.label}]
                  </span>
                  {step.timestamp && (
                    <span className="text-[10px] text-slate-500 font-mono">
                      {step.timestamp}
                    </span>
                  )}
                </div>
                <p className="text-slate-300 text-xs mt-0.5 leading-relaxed break-words">
                  {step.message}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
