import type { ChatMessage } from '../types';

export function generateObsidianMarkdown(message: ChatMessage, sessionId: string): string {
  const dateStr = new Date().toISOString().split('T')[0];
  const timeStr = new Date().toISOString();
  
  // Extract a brief title from the first line or use default
  const firstLine = message.content.split('\n')[0].replace(/^[#*\s-]+/, '').trim();
  const title = firstLine.length > 0 && firstLine.length < 60 ? firstLine : 'F.R.I. Financial Analysis';

  const frontmatter = [
    '---',
    `title: "${title.replace(/"/g, '\\"')}"`,
    `created: ${dateStr}`,
    `timestamp: "${timeStr}"`,
    `session_id: "${sessionId}"`,
    `source: "F.R.I. Multi-Agent AI"`,
    'tags:',
    '  - finance',
    '  - research',
    '  - FRI-analysis',
    '---',
    '',
  ].join('\n');

  let stepsSummary = '';
  if (message.steps && message.steps.length > 0) {
    stepsSummary = [
      '### Multi-Agent Pipeline Execution',
      ...message.steps.map((s) => `- **${s.agent.toUpperCase()}**: ${s.message}`),
      '',
      '---',
      '',
    ].join('\n');
  }

  return `${frontmatter}\n${stepsSummary}${message.content}\n`;
}

export function downloadMarkdownFile(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
