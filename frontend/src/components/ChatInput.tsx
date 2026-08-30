import React, { useRef, useEffect } from 'react';
import { Send, Square, Sparkles } from 'lucide-react';

interface ChatInputProps {
  input: string;
  setInput: (val: string) => void;
  onSubmit: () => void;
  onStop?: () => void;
  isLoading: boolean;
  onSelectSuggestion?: (prompt: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  input,
  setInput,
  onSubmit,
  onStop,
  isLoading,
  onSelectSuggestion,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && input.trim()) {
        onSubmit();
      }
    }
  };

  const suggestions = [
    'Discover Market News',
    'Analyze AAPL',
    'View Portfolio NAV',
    'Buy 10 NVDA',
  ];

  return (
    <div className="border-t border-slate-800 bg-[#0c1222]/95 backdrop-blur px-4 lg:px-8 py-4">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Quick prompt suggestion chips */}
        {onSelectSuggestion && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs no-scrollbar">
            <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1 flex-shrink-0">
              <Sparkles className="w-3 h-3 text-cyan-400" />
              Quick:
            </span>
            {suggestions.map((chip, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onSelectSuggestion(chip)}
                className="px-2.5 py-1 rounded-lg bg-slate-900/90 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-slate-100 text-[11px] font-medium whitespace-nowrap transition-colors cursor-pointer flex-shrink-0"
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* Text Input Box */}
        <div className="relative rounded-2xl bg-slate-950 border border-slate-800 focus-within:border-cyan-500/80 focus-within:ring-1 focus-within:ring-cyan-500/30 transition-all shadow-lg shadow-black/20">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask research query, stock ticker analysis, or investment command (Enter to send, Shift+Enter for newline)..."
            rows={2}
            className="w-full bg-transparent px-4 py-3.5 pr-24 text-slate-100 placeholder:text-slate-500 text-xs sm:text-sm resize-none outline-none font-sans leading-relaxed"
          />

          <div className="absolute right-3 bottom-3 flex items-center gap-2">
            {isLoading ? (
              <button
                type="button"
                onClick={onStop}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-600/90 hover:bg-rose-500 text-white text-xs font-semibold shadow-md transition-colors cursor-pointer"
                title="Stop generation"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={onSubmit}
                disabled={!input.trim()}
                className="flex items-center justify-center p-2 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white disabled:opacity-30 disabled:cursor-not-allowed shadow-md shadow-cyan-900/30 transition-all cursor-pointer"
                title="Send query"
                aria-label="Send query"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 font-mono px-1">
          <span>Targeting US Equities &amp; Live RSS feeds</span>
          <span>Press Enter to Send</span>
        </div>
      </div>
    </div>
  );
};
