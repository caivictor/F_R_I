import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Header } from '../components/Header';

describe('Header Component', () => {
  it('renders application branding and title correctly', () => {
    render(
      <Header
        health={{ status: 'ok', app: 'F.R.I.', version: '0.1.0' }}
        isHealthLoading={false}
        onNewSession={vi.fn()}
        onOpenPersonas={vi.fn()}
      />
    );

    expect(screen.getByText('F.R.I.')).toBeInTheDocument();
    expect(screen.getByText(/Financial Research & Investment/i)).toBeInTheDocument();
    expect(screen.getByText(/Multi-Agent AI/i)).toBeInTheDocument();
    expect(screen.getByText('v0.1.0')).toBeInTheDocument();
  });

  it('shows connecting state when health is loading', () => {
    render(
      <Header
        health={null}
        isHealthLoading={true}
        onNewSession={vi.fn()}
        onOpenPersonas={vi.fn()}
      />
    );

    expect(screen.getByText('Connecting...')).toBeInTheDocument();
  });

  it('shows offline state when health check fails', () => {
    render(
      <Header
        health={null}
        isHealthLoading={false}
        onNewSession={vi.fn()}
        onOpenPersonas={vi.fn()}
      />
    );

    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('triggers onNewSession and onOpenPersonas when clicked', () => {
    const handleNewSession = vi.fn();
    const handleOpenPersonas = vi.fn();

    render(
      <Header
        health={{ status: 'ok', app: 'F.R.I.', version: '0.1.0' }}
        isHealthLoading={false}
        onNewSession={handleNewSession}
        onOpenPersonas={handleOpenPersonas}
      />
    );

    const newSessionBtn = screen.getByRole('button', { name: /New Session/i });
    const personasBtn = screen.getByRole('button', { name: /Personas/i });

    fireEvent.click(newSessionBtn);
    expect(handleNewSession).toHaveBeenCalledTimes(1);

    fireEvent.click(personasBtn);
    expect(handleOpenPersonas).toHaveBeenCalledTimes(1);
  });
});
