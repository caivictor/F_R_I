import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.resolve(__dirname, '../screenshots');

test.describe('Phase 1 E2E Test Suite - F.R.I. App', () => {

  test('Backend API Health Check', async ({ request }) => {
    const response = await request.get('/api/health');
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe('ok');
    expect(body.app).toBe('F.R.I.');
    expect(body.version).toBe('0.1.0');
  });

  test('Backend API Personas Endpoints', async ({ request }) => {
    // 1. GET /api/personas
    const getRes = await request.get('/api/personas');
    expect(getRes.status()).toBe(200);
    const data = await getRes.json();
    expect(data.personas).toBeDefined();
    expect(data.defaults).toBeDefined();
    expect(data.personas.manager).toBeDefined();
    expect(data.personas.research).toBeDefined();
    expect(data.personas.analysis).toBeDefined();
    expect(data.personas.investment).toBeDefined();

    // 2. POST /api/personas to update manager
    const updatedDirective = 'You are an advanced test financial coordinator.';
    const putRes = await request.post('/api/personas', {
      data: {
        agent: 'manager',
        persona: updatedDirective
      }
    });
    expect(putRes.status()).toBe(200);
    const putData = await putRes.json();
    expect(putData.status).toBe('ok');
    expect(putData.personas.manager).toBe(updatedDirective);

    // 3. Verify updated
    const getUpdatedRes = await request.get('/api/personas');
    const updatedData = await getUpdatedRes.json();
    expect(updatedData.personas.manager).toBe(updatedDirective);

    // 4. Reset manager persona POST /api/personas/reset
    const resetRes = await request.post('/api/personas/reset', {
      data: { agent: 'manager' }
    });
    expect(resetRes.status()).toBe(200);
    const resetData = await resetRes.json();
    expect(resetData.status).toBe('ok');
    expect(resetData.personas.manager).toBe(data.defaults.manager);
  });

  test('Backend API Direct Chat Endpoint', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'What is your system status and available capabilities?'
      }
    });
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.response).toBeDefined();
    expect(typeof body.response).toBe('string');
    expect(body.response.length).toBeGreaterThan(10);
    expect(body.steps).toBeDefined();
    expect(Array.isArray(body.steps)).toBe(true);
  });

  test('Backend API Streaming Chat Endpoint', async ({ request }) => {
    const response = await request.post('/api/chat/stream', {
      data: {
        message: 'Analyze current market trends'
      }
    });
    expect(response.status()).toBe(200);
    expect(response.headers()['content-type']).toContain('text/event-stream');
    const rawText = await response.text();
    expect(rawText).toContain('"type": "step"');
    expect(rawText).toContain('"type": "done"');
    expect(rawText).toContain('data: ');
  });

  test('Frontend Root UI Loading and Layout', async ({ page }) => {
    await page.goto('/');

    // Wait for the app header and empty state
    await expect(page.locator('h1')).toContainText('F.R.I.');
    await expect(page.getByText('Financial Research & Investment')).toBeVisible();
    await expect(page.getByText('Multi-Agent AI')).toBeVisible();
    await expect(page.getByText('F.R.I. Financial Terminal')).toBeVisible();

    // Verify presence of prompt suggestions in empty state
    await expect(page.getByRole('button', { name: /Discover Market News/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Analyze AAPL/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /View Portfolio NAV/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /Buy 10 NVDA/i }).first()).toBeVisible();

    // Capture main layout screenshot
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'phase1-main.png'), fullPage: true });
  });

  test('Persona Settings Modal E2E Workflow', async ({ page }) => {
    await page.goto('/');

    // Open settings modal
    const personasBtn = page.getByRole('button', { name: /Personas/i });
    await personasBtn.click();

    // Modal title visible
    await expect(page.getByText('Agent Personas Configuration')).toBeVisible();
    await expect(page.getByRole('button', { name: /Manager Agent/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Research Agent/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Analysis Agent/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Investment Agent/i })).toBeVisible();

    // Switch tabs to Research Agent
    await page.getByRole('button', { name: /Research Agent/i }).click();
    const personaEditor = page.getByPlaceholder(/Enter custom agent directives/i);
    await expect(personaEditor).toBeVisible();

    // Capture modal screenshot
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'phase1-personas.png') });

    // Close modal
    const closeBtn = page.getByRole('button', { name: /Close Persona Settings/i });
    await closeBtn.click();
    await expect(page.getByText('Agent Personas Configuration')).not.toBeVisible();
  });

  test('Chat Interaction and Real-time Stream Flow', async ({ page }) => {
    await page.goto('/');

    // Click quick starter prompt "Discover Market News"
    const quickPrompt = page.getByRole('button', { name: /Discover Market News/i }).first();
    await quickPrompt.click();

    // User message should appear in chat
    await expect(page.getByText('Discover latest market news and key economic headlines', { exact: true })).toBeVisible();

    // Wait for the response to finish streaming and markdown to render
    await expect(page.getByText('F.R.I. Synthesis')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Market Themes')).toBeVisible({ timeout: 15000 });

    // Check export markdown button is visible on assistant message
    const copyBtn = page.getByRole('button', { name: /Copy Markdown/i });
    await expect(copyBtn.first()).toBeVisible({ timeout: 10000 });

    const exportBtn = page.getByRole('button', { name: /Export to Obsidian/i });
    await expect(exportBtn.first()).toBeVisible();

    // Capture chat response screenshot after stream completion
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'phase1-chat-response.png'), fullPage: true });
  });

  test('Custom Typed Prompt and Response Flow', async ({ page }) => {
    await page.goto('/');

    // Type a custom query in the chat input
    const inputArea = page.getByPlaceholder(/Ask research query/i);
    await inputArea.fill('Analyze AAPL valuation metrics and competitive position');

    // Submit
    const sendBtn = page.getByRole('button', { name: /Send query/i });
    await sendBtn.click();

    // Verify user message is in conversation
    await expect(page.getByText('Analyze AAPL valuation metrics and competitive position', { exact: true })).toBeVisible();

    // Verify response arrives
    await expect(page.getByText('Financial Health Scorecard')).toBeVisible({ timeout: 15000 });
    const copyBtn = page.getByRole('button', { name: /Copy Markdown/i });
    await expect(copyBtn.first()).toBeVisible({ timeout: 10000 });

    // Take screenshot of equity analysis
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'phase1-analysis-response.png'), fullPage: true });
  });

});
