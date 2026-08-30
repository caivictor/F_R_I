import { describe, it, expect } from 'vitest';
import { generateObsidianMarkdown } from '../utils/exportMarkdown';
import type { ChatMessage } from '../types';

describe('exportMarkdown utility', () => {
  it('generates markdown with YAML frontmatter and multi-agent trace', () => {
    const msg: ChatMessage = {
      id: 'test-id-123456',
      role: 'assistant',
      content: '# AAPL Valuation Analysis\n\nStock looks strong.',
      timestamp: '10:00:00 AM',
      steps: [
        { agent: 'manager', message: 'Task routed' },
        { agent: 'analysis', message: 'Ratios fetched' },
      ],
    };

    const result = generateObsidianMarkdown(msg, 'session-test-001');

    expect(result).toContain('---');
    expect(result).toContain('title: "AAPL Valuation Analysis"');
    expect(result).toContain('session_id: "session-test-001"');
    expect(result).toContain('source: "F.R.I. Multi-Agent AI"');
    expect(result).toContain('tags:');
    expect(result).toContain('- **MANAGER**: Task routed');
    expect(result).toContain('- **ANALYSIS**: Ratios fetched');
    expect(result).toContain('# AAPL Valuation Analysis');
  });
});
