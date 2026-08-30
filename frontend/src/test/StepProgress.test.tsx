import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { StepProgress } from '../components/StepProgress';
import type { AgentStep } from '../types';

describe('StepProgress Component', () => {
  it('renders nothing when steps list is empty', () => {
    const { container } = render(<StepProgress steps={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders multi-agent trace steps with badges', () => {
    const steps: AgentStep[] = [
      { agent: 'manager', message: 'Evaluating incoming prompt', timestamp: '10:00:01 AM' },
      { agent: 'research', message: 'Scanning Google News RSS', timestamp: '10:00:02 AM' },
      { agent: 'analysis', message: 'Fetching yfinance fundamentals', timestamp: '10:00:03 AM' },
      { agent: 'investment', message: 'Checking portfolio allocations', timestamp: '10:00:04 AM' },
    ];

    render(<StepProgress steps={steps} />);

    expect(screen.getByText(/Multi-Agent Pipeline Trace/i)).toBeInTheDocument();
    expect(screen.getByText('4 steps')).toBeInTheDocument();
    expect(screen.getByText('[Manager]')).toBeInTheDocument();
    expect(screen.getByText('[Research Agent]')).toBeInTheDocument();
    expect(screen.getByText('[Analysis Agent]')).toBeInTheDocument();
    expect(screen.getByText('[Investment Agent]')).toBeInTheDocument();
    expect(screen.getByText('Evaluating incoming prompt')).toBeInTheDocument();
    expect(screen.getByText('Scanning Google News RSS')).toBeInTheDocument();
  });
});
