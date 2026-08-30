import React from 'react';
import { Newspaper, LineChart, Wallet, ShoppingCart, ShieldCheck } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt }) => {
  const quickActions = [
    {
      title: 'Discover Market News',
      desc: 'Scan Google News RSS feeds for top macro headlines and trends',
      icon: Newspaper,
      color: 'text-emerald-400',
      border: 'border-emerald-800/40 hover:border-emerald-500/60',
      bg: 'bg-emerald-950/20 hover:bg-emerald-950/40',
      prompt: 'Discover latest market news and key economic headlines',
    },
    {
      title: 'Analyze AAPL',
      desc: 'Fetch real-time fundamental & technical ratios via yfinance',
      icon: LineChart,
      color: 'text-amber-400',
      border: 'border-amber-800/40 hover:border-amber-500/60',
      bg: 'bg-amber-950/20 hover:bg-amber-950/40',
      prompt: 'Analyze AAPL fundamentals, valuation metrics, and recent performance',
    },
    {
      title: 'View Portfolio NAV',
      desc: 'Inspect cash balance, positions, allocations, and profit/loss',
      icon: Wallet,
      color: 'text-cyan-400',
      border: 'border-cyan-800/40 hover:border-cyan-500/60',
      bg: 'bg-cyan-950/20 hover:bg-cyan-950/40',
      prompt: 'View portfolio NAV, current positions, and cash balance',
    },
    {
      title: 'Buy 10 NVDA',
      desc: 'Simulate safety-checked order proposal and trade allocation',
      icon: ShoppingCart,
      color: 'text-indigo-400',
      border: 'border-indigo-800/40 hover:border-indigo-500/60',
      bg: 'bg-indigo-950/20 hover:bg-indigo-950/40',
      prompt: 'Buy 10 shares of NVDA at market price',
    },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center max-w-4xl mx-auto px-4 py-8 text-center animate-in fade-in duration-300">
      {/* Central Terminal Icon */}
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-600/30 via-indigo-600/30 to-purple-600/30 border border-cyan-500/30 flex items-center justify-center mb-6 shadow-xl shadow-cyan-950/40">
        <ShieldCheck className="w-8 h-8 text-cyan-400" />
      </div>

      <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100 font-sans">
        F.R.I. Financial Terminal
      </h2>
      <p className="mt-2 text-sm text-slate-400 max-w-lg leading-relaxed">
        Multi-agent autonomous intelligence for market research, stock analysis, and portfolio investment execution.
      </p>

      {/* Grid of quick prompts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mt-8 w-full">
        {quickActions.map((action, idx) => {
          const Icon = action.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectPrompt(action.prompt)}
              className={`p-4 rounded-xl border ${action.border} ${action.bg} text-left transition-all duration-150 active:scale-[0.98] cursor-pointer group shadow-sm`}
            >
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800 flex-shrink-0">
                  <Icon className={`w-4 h-4 ${action.color} group-hover:scale-110 transition-transform`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-semibold text-slate-200 group-hover:text-slate-100">
                    {action.title}
                  </div>
                  <div className="text-[11px] text-slate-400 line-clamp-1 mt-0.5">
                    {action.desc}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
