import React, { useState, useEffect } from 'react';
import { X, Bot, ShieldCheck, Search, TrendingUp, PieChart, RotateCcw, Save, Check, AlertCircle } from 'lucide-react';
import { fetchPersonas, updatePersona, resetPersona } from '../services/api';
import type { AgentType } from '../types';

interface PersonaModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface AgentMeta {
  key: AgentType;
  name: string;
  roleDescription: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  activeColor: string;
  borderColor: string;
}

const AGENT_LIST: AgentMeta[] = [
  {
    key: 'manager',
    name: 'Manager Agent',
    roleDescription: 'Routes user queries, synthesizes final reports, coordinates sub-agents, and enforces trade safety.',
    icon: ShieldCheck,
    color: 'text-indigo-400',
    activeColor: 'bg-indigo-950/60 border-indigo-500/50 text-indigo-200',
    borderColor: 'border-indigo-500/30',
  },
  {
    key: 'research',
    name: 'Research Agent',
    roleDescription: 'Fetches real-time market news from Google News RSS and gathers market context.',
    icon: Search,
    color: 'text-emerald-400',
    activeColor: 'bg-emerald-950/60 border-emerald-500/50 text-emerald-200',
    borderColor: 'border-emerald-500/30',
  },
  {
    key: 'analysis',
    name: 'Analysis Agent',
    roleDescription: 'Retrieves fundamental/technical metrics via yfinance, strictly validates US public tickers, and computes ratios.',
    icon: TrendingUp,
    color: 'text-amber-400',
    activeColor: 'bg-amber-950/60 border-amber-500/50 text-amber-200',
    borderColor: 'border-amber-500/30',
  },
  {
    key: 'investment',
    name: 'Investment Agent',
    roleDescription: 'Tracks SQLite portfolio, calculates NAV, checks buying power, and generates order proposals.',
    icon: PieChart,
    color: 'text-cyan-400',
    activeColor: 'bg-cyan-950/60 border-cyan-500/50 text-cyan-200',
    borderColor: 'border-cyan-500/30',
  },
];

export const PersonaModal: React.FC<PersonaModalProps> = ({ isOpen, onClose }) => {
  const [activeAgent, setActiveAgent] = useState<AgentType>('manager');
  const [personas, setPersonas] = useState<Record<string, string>>({});
  const [defaults, setDefaults] = useState<Record<string, string>>({});
  const [currentText, setCurrentText] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadPersonas();
    }
  }, [isOpen]);

  useEffect(() => {
    if (personas[activeAgent] !== undefined) {
      setCurrentText(personas[activeAgent]);
    }
  }, [activeAgent, personas]);

  const loadPersonas = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await fetchPersonas();
      setPersonas(data.personas || {});
      setDefaults(data.defaults || {});
      if (data.personas && data.personas[activeAgent]) {
        setCurrentText(data.personas[activeAgent]);
      }
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to load personas');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      await updatePersona(activeAgent, currentText);
      setPersonas((prev) => ({ ...prev, [activeAgent]: currentText }));
      setSuccessMessage(`Saved custom persona for ${activeAgent.toUpperCase()}`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to save persona');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetAgent = async () => {
    setIsSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      await resetPersona(activeAgent);
      const defaultVal = defaults[activeAgent] || '';
      setPersonas((prev) => ({ ...prev, [activeAgent]: defaultVal }));
      setCurrentText(defaultVal);
      setSuccessMessage(`Reset ${activeAgent.toUpperCase()} to default system persona`);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to reset persona');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetAll = async () => {
    if (!window.confirm('Are you sure you want to reset all agent personas to their factory defaults?')) {
      return;
    }
    setIsSaving(true);
    setSuccessMessage(null);
    setErrorMessage(null);
    try {
      await resetPersona();
      setPersonas({ ...defaults });
      setCurrentText(defaults[activeAgent] || '');
      setSuccessMessage('Reset all agent personas to factory defaults');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to reset all personas');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  const currentMeta = AGENT_LIST.find((a) => a.key === activeAgent) || AGENT_LIST[0];
  const CurrentIcon = currentMeta.icon;
  const isModified = currentText !== (defaults[activeAgent] || '');

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl max-h-[90vh] flex flex-col bg-[#0f172a] border border-slate-700 rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#090d16]/80">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-950/80 border border-indigo-800 text-indigo-400">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                Agent Personas Configuration
              </h2>
              <p className="text-xs text-slate-400">
                Customize system prompts and behavioral instructions for each multi-agent specialist.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            aria-label="Close Persona Settings"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-hidden flex flex-col md:flex-row">
          {/* Left Agent Selector Sidebar */}
          <div className="w-full md:w-64 border-b md:border-b-0 md:border-r border-slate-800 p-4 space-y-2 bg-[#0c1222]/60 overflow-y-auto">
            <div className="text-[11px] font-mono uppercase tracking-wider text-slate-400 px-2 py-1">
              Select Specialist
            </div>
            {AGENT_LIST.map((agent) => {
              const Icon = agent.icon;
              const isSelected = activeAgent === agent.key;
              const hasCustom = personas[agent.key] && personas[agent.key] !== defaults[agent.key];

              return (
                <button
                  key={agent.key}
                  onClick={() => setActiveAgent(agent.key)}
                  className={`w-full text-left p-3 rounded-xl border transition-all flex items-start gap-3 cursor-pointer ${
                    isSelected
                      ? agent.activeColor
                      : 'bg-slate-900/40 border-slate-800 hover:bg-slate-800/60 text-slate-300'
                  }`}
                >
                  <div className="mt-0.5">
                    <Icon className={`w-4 h-4 ${isSelected ? agent.color : 'text-slate-400'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold">{agent.name}</span>
                      {hasCustom && (
                        <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700/50">
                          CUSTOM
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                      {agent.roleDescription}
                    </p>
                  </div>
                </button>
              );
            })}

            <div className="pt-4 mt-4 border-t border-slate-800">
              <button
                onClick={handleResetAll}
                disabled={isSaving || isLoading}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
              >
                <RotateCcw className="w-3.5 h-3.5 text-rose-400" />
                <span>Reset All Defaults</span>
              </button>
            </div>
          </div>

          {/* Right Editor Area */}
          <div className="flex-1 p-6 flex flex-col overflow-y-auto bg-[#0b0f19]">
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center text-slate-400 text-sm">
                Loading persona configuration...
              </div>
            ) : (
              <div className="flex-1 flex flex-col">
                {/* Agent Header & Description */}
                <div className="mb-4 pb-4 border-b border-slate-800/80 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-slate-900 border ${currentMeta.borderColor}`}>
                      <CurrentIcon className={`w-5 h-5 ${currentMeta.color}`} />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                        {currentMeta.name}
                        {isModified ? (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/60">
                            Modified
                          </span>
                        ) : (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                            Default
                          </span>
                        )}
                      </h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {currentMeta.roleDescription}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Notifications */}
                {successMessage && (
                  <div className="mb-3 p-3 rounded-lg bg-emerald-950/60 border border-emerald-800/80 text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
                    <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span>{successMessage}</span>
                  </div>
                )}
                {errorMessage && (
                  <div className="mb-3 p-3 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2 animate-in fade-in">
                    <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                    <span>{errorMessage}</span>
                  </div>
                )}

                {/* Textarea Editor */}
                <div className="flex-1 flex flex-col min-h-[220px]">
                  <label className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 flex items-center justify-between">
                    <span>System Prompt / Directive</span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {currentText.length} chars
                    </span>
                  </label>
                  <textarea
                    value={currentText}
                    onChange={(e) => setCurrentText(e.target.value)}
                    rows={12}
                    className="w-full flex-1 p-3.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-slate-200 text-xs font-mono leading-relaxed resize-none outline-none transition-all placeholder:text-slate-600"
                    placeholder="Enter custom agent directives, style constraints, or analytical rules..."
                  />
                </div>

                {/* Editor Bottom Actions */}
                <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between gap-3">
                  <button
                    onClick={handleResetAgent}
                    disabled={isSaving || !isModified}
                    className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 text-xs font-medium transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reset Agent Default</span>
                  </button>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={onClose}
                      className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors cursor-pointer"
                    >
                      Close
                    </button>
                    <button
                      onClick={handleSave}
                      disabled={isSaving}
                      className="flex items-center gap-2 px-5 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-md shadow-indigo-900/30 transition-all cursor-pointer disabled:opacity-50"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>{isSaving ? 'Saving...' : 'Save Persona'}</span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
