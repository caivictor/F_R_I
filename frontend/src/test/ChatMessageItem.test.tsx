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

  it('renders portfolio markdown tables cleanly', () => {
    const portfolioMsg: ChatMessage = {
      id: 'msg-portfolio',
      role: 'assistant',
      content: `### Current Portfolio Holdings

| Symbol | Shares | Avg Cost | Current Price | Unrealized P&L | Market Value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| AAPL | 50 | $150.00 | $175.50 | +$1,275.00 (+17.0%) | $8,775.00 |
| MSFT | 30 | $310.00 | $340.20 | +$906.00 (+9.7%) | $10,206.00 |
| NVDA | 25 | $420.00 | $460.00 | +$1,000.00 (+9.5%) | $11,500.00 |

**Total Portfolio Value:** $30,481.00`,
      timestamp: '10:05:00 AM',
    };

    render(<ChatMessageItem message={portfolioMsg} sessionId="sess-1" />);

    expect(screen.getByText(/Current Portfolio Holdings/i)).toBeInTheDocument();
    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Shares')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('NVDA')).toBeInTheDocument();
    expect(screen.getByText('$8,775.00')).toBeInTheDocument();
    expect(screen.getByText('$10,206.00')).toBeInTheDocument();
    expect(screen.getByText('$11,500.00')).toBeInTheDocument();
  });

  it('renders transaction logs cleanly', () => {
    const txLogMsg: ChatMessage = {
      id: 'msg-tx-log',
      role: 'assistant',
      content: `### Portfolio Transaction History

| Tx ID | Date | Action | Symbol | Quantity | Price | Total Value | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| TX-101 | 2026-08-28 | BUY | AAPL | 50 | $150.00 | $7,500.00 | EXECUTED |
| TX-102 | 2026-08-29 | BUY | MSFT | 30 | $310.00 | $9,300.00 | EXECUTED |

*All transactions settled successfully in paper trading ledger.*`,
      timestamp: '10:10:00 AM',
    };

    render(<ChatMessageItem message={txLogMsg} sessionId="sess-1" />);

    expect(screen.getByText(/Portfolio Transaction History/i)).toBeInTheDocument();
    expect(screen.getByText('Tx ID')).toBeInTheDocument();
    expect(screen.getByText('TX-101')).toBeInTheDocument();
    expect(screen.getByText('TX-102')).toBeInTheDocument();
    expect(screen.getAllByText('BUY')).toHaveLength(2);
    expect(screen.getAllByText('EXECUTED')).toHaveLength(2);
    expect(screen.getByText('$7,500.00')).toBeInTheDocument();
    expect(screen.getByText('$9,300.00')).toBeInTheDocument();
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
