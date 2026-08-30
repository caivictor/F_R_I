import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.resolve(__dirname, '../screenshots');

test.describe('Phase 2 E2E Test Suite - Research, Analysis & Manager Self-Healing', () => {

  test('Backend API - Research Agent Google News & RSS parsing', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'Discover latest market news and key economic headlines'
      }
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.response).toBeDefined();
    expect(data.steps).toBeDefined();
    
    // Check steps include research agent
    const researchStep = data.steps.find((s: any) => s.agent === 'research');
    expect(researchStep).toBeDefined();
    expect(researchStep.message).toContain('Research Agent');

    // Check response content format
    expect(data.response).toContain('Market Research Findings');
    expect(data.response).toContain('Market Themes');
  });

  test('Backend API - Analysis Agent Financial Metrics & Dossier', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'Analyze AAPL valuation metrics and competitive position'
      }
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.response).toBeDefined();
    
    // Check Analysis Agent stepped in
    const analysisStep = data.steps.find((s: any) => s.agent === 'analysis');
    expect(analysisStep).toBeDefined();

    // Check dossier sections and metrics
    expect(data.response).toContain('Financial Health Scorecard');
    expect(data.response).toContain('Market Cap');
    expect(data.response).toContain('Economic Moat');
    expect(data.response).toContain('Investment Thesis');
    expect(data.response).toContain('Bull vs. Bear');
  });

  test('Backend API - Analysis Agent Private Company Guardrail', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'Analyze OpenAI fundamentals and valuation'
      }
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.response).toContain('Analysis Rejection');
    expect(data.response.toLowerCase()).toContain('private company');
  });

  test('Backend API - Analysis Agent Non-US / OTC Listing Guardrail', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'Analyze 0700.HK valuation and growth'
      }
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.response).toContain('Analysis Rejection');
    expect(data.response).toContain('non-US');
  });

  test('Backend API - Multi-Agent End-to-End Discovery Pipeline', async ({ request }) => {
    const response = await request.post('/api/chat', {
      data: {
        message: 'Discover top tech stories and analyze promising stocks'
      }
    });
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.response).toContain('Executive Investment Discovery Briefing');
    expect(data.response).toContain('Market Research Findings');
    expect(data.response).toContain('Quantitative & Fundamental Analysis');
    
    const agentsInvolved = data.steps.map((s: any) => s.agent);
    expect(agentsInvolved).toContain('research');
    expect(agentsInvolved).toContain('analysis');
  });

  test('UI E2E - Market Research News Trigger and Render', async ({ page }) => {
    await page.goto('/');

    // Click starter prompt "Discover Market News"
    const newsBtn = page.getByRole('button', { name: /Discover Market News/i }).first();
    await newsBtn.click();

    // Verify user message appears
    await expect(page.getByText('Discover latest market news and key economic headlines', { exact: true })).toBeVisible();

    // Verify streaming step indicator and response
    await expect(page.getByText('F.R.I. Synthesis')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Market Themes')).toBeVisible({ timeout: 15000 });
  });

  test('UI E2E - Single Stock Equity Analysis and Screenshot Capture', async ({ page }) => {
    await page.goto('/');

    // Type AAPL analysis prompt in chat input
    const inputArea = page.getByPlaceholder(/Ask research query/i);
    await inputArea.fill('Analyze AAPL valuation metrics and competitive position');
    const sendBtn = page.getByRole('button', { name: /Send query/i });
    await sendBtn.click();

    // Verify response arrives with financial metrics
    await expect(page.getByText('Financial Health Scorecard')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Economic Moat & Competitive Advantage')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('Bull vs. Bear Risk Assessment')).toBeVisible({ timeout: 15000 });

    // Capture screenshot for Phase 2 Research & Analysis verification
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'phase2-research-analysis.png'),
      fullPage: true
    });
  });

  test('UI E2E - Private Company Rejection Guardrail in Chat', async ({ page }) => {
    await page.goto('/');

    const inputArea = page.getByPlaceholder(/Ask research query/i);
    await inputArea.fill('Analyze SpaceX valuation and moat');
    const sendBtn = page.getByRole('button', { name: /Send query/i });
    await sendBtn.click();

    // Verify rejection guardrail rendered in chat
    await expect(page.getByText('Analysis Rejection')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/SpaceX is a private company/i)).toBeVisible({ timeout: 15000 });
  });

  test('UI E2E - Multi-turn Pronoun Resolution (NVDA -> its metrics)', async ({ page }) => {
    await page.goto('/');

    // Turn 1: Analyze NVDA
    const inputArea = page.getByPlaceholder(/Ask research query/i);
    await inputArea.fill('Analyze NVDA');
    const sendBtn = page.getByRole('button', { name: /Send query/i });
    await sendBtn.click();

    await expect(page.getByText('Financial Health Scorecard')).toBeVisible({ timeout: 15000 });

    // Turn 2: Ask about its debt to equity
    await inputArea.fill('What is its debt to equity and valuation?');
    await sendBtn.click();

    // Verify response resolves NVDA context
    await expect(page.getByText(/NVDA|NVIDIA/i).last()).toBeVisible({ timeout: 15000 });
  });

});
