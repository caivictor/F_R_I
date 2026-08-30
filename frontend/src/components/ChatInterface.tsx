import React, { useRef, useEffect } from 'react';
import type { ChatMessage } from '../types';
import { ChatMessageItem } from './ChatMessageItem';
import { EmptyState } from './EmptyState';
import { ChatInput } from './ChatInput';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  sessionId: string;
  input: string;
  setInput: (val: string) => void;
  onSubmit: (prompt?: string) => void;
  onStop?: () => void;
  isLoading: boolean;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  sessionId,
  input,
  setInput,
  onSubmit,
  onStop,
  isLoading,
}) => {
  const scrollEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    scrollEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, messages[messages.length - 1]?.content, messages[messages.length - 1]?.steps]);

  const handleSelectSuggestion = (prompt: string) => {
    setInput(prompt);
    onSubmit(prompt);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#090d16]">
      {/* Scrollable messages container */}
      <div className="flex-1 overflow-y-auto px-4 lg:px-8 py-6">
        <div className="max-w-4xl mx-auto min-h-full flex flex-col">
          {messages.length === 0 ? (
            <EmptyState onSelectPrompt={handleSelectSuggestion} />
          ) : (
            <div className="space-y-2">
              {messages.map((msg) => (
                <ChatMessageItem key={msg.id} message={msg} sessionId={sessionId} />
              ))}
              <div ref={scrollEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* Fixed bottom input */}
      <ChatInput
        input={input}
        setInput={setInput}
        onSubmit={() => onSubmit()}
        onStop={onStop}
        isLoading={isLoading}
        onSelectSuggestion={handleSelectSuggestion}
      />
    </div>
  );
};
