import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, Download, Bot, User, Clock } from 'lucide-react';
import type { ChatMessage } from '../types';
import { StepProgress } from './StepProgress';
import { generateObsidianMarkdown, downloadMarkdownFile } from '../utils/exportMarkdown';

interface ChatMessageItemProps {
  message: ChatMessage;
  sessionId: string;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({ message, sessionId }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard fallback
      const textArea = document.createElement('textarea');
      textArea.value = message.content;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExport = () => {
    const markdown = generateObsidianMarkdown(message, sessionId);
    const dateStr = new Date().toISOString().split('T')[0];
    const filename = `FRI-Analysis-${dateStr}-${message.id.slice(0, 8)}.md`;
    downloadMarkdownFile(markdown, filename);
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
        <div className="max-w-2xl flex items-start gap-3 flex-row-reverse">
          <div className="w-8 h-8 rounded-lg bg-cyan-600/30 border border-cyan-500/40 flex items-center justify-center flex-shrink-0 text-cyan-300">
            <User className="w-4 h-4" />
          </div>
          <div className="bg-gradient-to-r from-cyan-950/80 to-slate-900 border border-cyan-800/40 rounded-2xl rounded-tr-none px-4 py-3 text-slate-100 shadow-md">
            <p className="text-xs sm:text-sm whitespace-pre-wrap leading-relaxed font-sans">
              {message.content}
            </p>
            <div className="mt-1 flex items-center justify-end gap-1 text-[10px] text-cyan-400/70 font-mono">
              <Clock className="w-3 h-3" />
              <span>{message.timestamp}</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-8 animate-in fade-in slide-in-from-bottom-2 duration-200">
      <div className="w-full max-w-4xl flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600/30 to-purple-600/30 border border-indigo-500/40 flex items-center justify-center flex-shrink-0 text-indigo-300 mt-1">
          <Bot className="w-4 h-4" />
        </div>

        <div className="flex-1 min-w-0 bg-[#0e1628]/90 border border-slate-800 rounded-2xl rounded-tl-none p-5 shadow-lg shadow-black/40">
          {/* Header Bar */}
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/80">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-indigo-300 font-mono">
                F.R.I. Synthesis
              </span>
              {message.isStreaming && (
                <span className="flex items-center gap-1 text-[10px] font-mono text-cyan-400 bg-cyan-950/80 border border-cyan-800/60 px-2 py-0.5 rounded-full animate-pulse">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                  Generating...
                </span>
              )}
            </div>
            <span className="text-[10px] text-slate-500 font-mono">{message.timestamp}</span>
          </div>

          {/* Step Progress Trace */}
          {message.steps && message.steps.length > 0 && (
            <StepProgress steps={message.steps} isStreaming={message.isStreaming} />
          )}

          {/* Markdown Content */}
          <div className="markdown-body text-slate-200 text-xs sm:text-sm leading-relaxed prose prose-invert max-w-none">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ ...props }) => (
                  <h1 className="text-lg font-bold text-slate-100 mt-4 mb-2 pb-1 border-b border-slate-800 font-sans" {...props} />
                ),
                h2: ({ ...props }) => (
                  <h2 className="text-base font-semibold text-cyan-300 mt-3 mb-2 font-sans" {...props} />
                ),
                h3: ({ ...props }) => (
                  <h3 className="text-sm font-semibold text-indigo-300 mt-2 mb-1 font-sans" {...props} />
                ),
                ul: ({ ...props }) => <ul className="list-disc list-inside space-y-1 my-2 text-slate-300" {...props} />,
                ol: ({ ...props }) => <ol className="list-decimal list-inside space-y-1 my-2 text-slate-300" {...props} />,
                p: ({ ...props }) => <p className="my-2 leading-relaxed" {...props} />,
                strong: ({ ...props }) => <strong className="font-semibold text-slate-100" {...props} />,
                code: ({ className, children, ...props }) => {
                  const isInline = !className;
                  if (isInline) {
                    return (
                      <code className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 font-mono text-[11px] border border-slate-700" {...props}>
                        {children}
                      </code>
                    );
                  }
                  return (
                    <code className="block p-3 rounded-lg bg-slate-950 font-mono text-xs text-slate-300 border border-slate-800 overflow-x-auto" {...props}>
                      {children}
                    </code>
                  );
                },
                table: ({ ...props }) => (
                  <div className="overflow-x-auto my-3 rounded-lg border border-slate-800 bg-slate-900/50">
                    <table className="w-full text-xs text-left border-collapse" {...props} />
                  </div>
                ),
                th: ({ ...props }) => (
                  <th className="px-3.5 py-2 bg-slate-900 border-b border-slate-800 text-cyan-400 font-semibold font-mono text-[11px] uppercase tracking-wider" {...props} />
                ),
                td: ({ ...props }) => (
                  <td className="px-3.5 py-2 border-b border-slate-800/60 text-slate-300 font-sans" {...props} />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Action Toolbar */}
          {!message.isStreaming && (
            <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-end gap-2 text-xs">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition-colors text-[11px] font-medium cursor-pointer"
                title="Copy Markdown to clipboard"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-slate-400" />
                    <span>Copy Markdown</span>
                  </>
                )}
              </button>

              <button
                onClick={handleExport}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 hover:border-slate-700 transition-colors text-[11px] font-medium cursor-pointer"
                title="Export report formatted for Obsidian with YAML frontmatter"
              >
                <Download className="w-3.5 h-3.5 text-cyan-400" />
                <span>Export to Obsidian (.md)</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
