import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatMessageItem } from '../components/ChatMessageItem';
import type { ChatMessage } from '../types';

describe('ChatMessageItem Component', () => {
  beforeEach(() => {
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  it('renders user message', () => {
    const userMsg: ChatMessage = {
      id: 'msg-1',
      role: 'user',
      content: 'Analyze NVDA stock',
      timestamp: '10:00:00 AM',
    };

    render(<ChatMessageItem message={userMsg} sessionId="sess-1" />);

    expect(screen.getByText('Analyze NVDA stock')).toBeInTheDocument();
    expect(screen.getByText('10:00:00 AM')).toBeInTheDocument();
  });

  it('renders assistant message with rich markdown and financial table', () => {
    const assistantMsg: ChatMessage = {
      id: 'msg-2',
      role: 'assistant',
      content: '### Valuation Analysis\n\n| Metric | Value |\n| --- | --- |\n| P/E Ratio | 35.4 |\n| Market Cap | $2.5T |\n\nRecommendation: **HOLD**',
      timestamp: '10:00:05 AM',
      steps: [
        { agent: 'manager', message: 'Routing analysis task to Analysis Agent' },
        { agent: 'analysis', message: 'Fetched fundamental metrics for NVDA' },
      ],
    };

    render(<ChatMessageItem message={assistantMsg} sessionId="sess-1" />);

    expect(screen.getByText(/Valuation Analysis/i)).toBeInTheDocument();
    expect(screen.getByText('Metric')).toBeInTheDocument();
    expect(screen.getByText('P/E Ratio')).toBeInTheDocument();
    expect(screen.getByText('35.4')).toBeInTheDocument();
    expect(screen.getByText('HOLD')).toBeInTheDocument();
    expect(screen.getByText(/Routing analysis task to Analysis Agent/i)).toBeInTheDocument();
    expect(screen.getByText(/Fetched fundamental metrics for NVDA/i)).toBeInTheDocument();
  });

  it('handles copy markdown button click', async () => {
    const assistantMsg: ChatMessage = {
      id: 'msg-3',
      role: 'assistant',
      content: 'Market news summary content',
      timestamp: '10:01:00 AM',
    };

    render(<ChatMessageItem message={assistantMsg} sessionId="sess-1" />);

    const copyBtn = screen.getByRole('button', { name: /Copy Markdown/i });
    fireEvent.click(copyBtn);

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith('Market news summary content');
    expect(await screen.findByText('Copied')).toBeInTheDocument();
  });
});
