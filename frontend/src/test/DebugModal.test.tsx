import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DebugModal } from '../components/DebugModal';

describe('DebugModal Component', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        session_id: 'sess_test_1',
        session_title: 'Active Session',
        total_logs: 1,
        debug_logs: [
          {
            id: 1,
            session_id: 'sess_test_1',
            timestamp: '12:00:00',
            agent: 'manager',
            model: 'gemini-2.5-flash',
            prompt: 'Hello',
            status: 'turn_completed',
            latency_ms: 15.0,
          },
        ],
        messages: [{ role: 'user', content: 'Hello', timestamp: '12:00:00' }],
        active_memory: {
          last_ticker: 'AAPL',
          last_discovered_tickers: ['AAPL', 'MSFT'],
          summary: 'Prior research context',
        },
      }),
    }));
  });

  it('does not render when isOpen is false', () => {
    const { container } = render(
      <DebugModal
        isOpen={false}
        sessionId="sess_test_1"
        onClose={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders debug inspector title and tabs when open', async () => {
    render(
      <DebugModal
        isOpen={true}
        sessionId="sess_test_1"
        onClose={vi.fn()}
      />
    );

    expect(screen.getByText(/LLM Context & Debug Inspector/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Context & Prompts/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Conversation/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Active Memory/i })).toBeInTheDocument();
  });

  it('switches tabs on tab click', async () => {
    render(
      <DebugModal
        isOpen={true}
        sessionId="sess_test_1"
        onClose={vi.fn()}
      />
    );

    const memoryTab = screen.getByRole('button', { name: /Active Memory/i });
    fireEvent.click(memoryTab);

    await waitFor(() => {
      expect(screen.getByText(/Persistent Context State/i)).toBeInTheDocument();
    });
  });
});
