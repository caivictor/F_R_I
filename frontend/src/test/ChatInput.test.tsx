import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ChatInput } from '../components/ChatInput';

describe('ChatInput Component', () => {
  it('updates input value and handles submit on Enter', () => {
    const handleSetInput = vi.fn();
    const handleSubmit = vi.fn();

    render(
      <ChatInput
        input="Analyze TSLA"
        setInput={handleSetInput}
        onSubmit={handleSubmit}
        isLoading={false}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask research query/i);
    expect(textarea).toHaveValue('Analyze TSLA');

    fireEvent.change(textarea, { target: { value: 'Analyze NVDA' } });
    expect(handleSetInput).toHaveBeenCalledWith('Analyze NVDA');

    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
    expect(handleSubmit).toHaveBeenCalledTimes(1);
  });

  it('does not submit on Shift+Enter (allows newline)', () => {
    const handleSubmit = vi.fn();

    render(
      <ChatInput
        input="Analyze TSLA"
        setInput={vi.fn()}
        onSubmit={handleSubmit}
        isLoading={false}
      />
    );

    const textarea = screen.getByPlaceholderText(/Ask research query/i);
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true });
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('calls onSelectSuggestion when quick chip is clicked', () => {
    const handleSelectSuggestion = vi.fn();

    render(
      <ChatInput
        input=""
        setInput={vi.fn()}
        onSubmit={vi.fn()}
        isLoading={false}
        onSelectSuggestion={handleSelectSuggestion}
      />
    );

    const chip = screen.getByText('Analyze AAPL');
    fireEvent.click(chip);
    expect(handleSelectSuggestion).toHaveBeenCalledWith('Analyze AAPL');
  });
});
