import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PersonaModal } from '../components/PersonaModal';
import * as api from '../services/api';

vi.mock('../services/api', () => ({
  fetchPersonas: vi.fn(),
  updatePersona: vi.fn(),
  resetPersona: vi.fn(),
}));

describe('PersonaModal Component', () => {
  const mockPersonas = {
    manager: 'Default Manager Persona',
    research: 'Default Research Persona',
    analysis: 'Default Analysis Persona',
    investment: 'Default Investment Persona',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchPersonas).mockResolvedValue({
      personas: { ...mockPersonas },
      defaults: { ...mockPersonas },
    });
  });

  it('renders modal when open', async () => {
    render(<PersonaModal isOpen={true} onClose={vi.fn()} />);

    expect(screen.getByText('Agent Personas Configuration')).toBeInTheDocument();
    expect(await screen.findByText('Manager Agent')).toBeInTheDocument();
    expect(screen.getByText('Research Agent')).toBeInTheDocument();
    expect(screen.getByText('Analysis Agent')).toBeInTheDocument();
    expect(screen.getByText('Investment Agent')).toBeInTheDocument();
  });

  it('allows switching specialist tabs', async () => {
    render(<PersonaModal isOpen={true} onClose={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByDisplayValue('Default Manager Persona')).toBeInTheDocument();
    });

    const researchTab = screen.getByRole('button', { name: /Research Agent/i });
    fireEvent.click(researchTab);

    expect(await screen.findByDisplayValue('Default Research Persona')).toBeInTheDocument();
  });

  it('saves updated persona', async () => {
    vi.mocked(api.updatePersona).mockResolvedValue({ status: 'ok' });

    render(<PersonaModal isOpen={true} onClose={vi.fn()} />);

    const textarea = await screen.findByDisplayValue('Default Manager Persona');
    fireEvent.change(textarea, { target: { value: 'Custom Manager Directive' } });

    const saveBtn = screen.getByRole('button', { name: /Save Persona/i });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(api.updatePersona).toHaveBeenCalledWith('manager', 'Custom Manager Directive');
      expect(screen.getByText(/Saved custom persona/i)).toBeInTheDocument();
    });
  });
});
