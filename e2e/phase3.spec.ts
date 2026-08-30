import { test, expect } from '@playwright/test';
import path from 'path';

const SCREENSHOT_DIR = path.resolve(__dirname, '../screenshots');

test.describe('Phase 3 E2E Test Suite - SQLite Portfolio Tracking, Cash Management & Trade Confirmation', () => {

  test('Backend API - Reset, Deposit, Withdraw, Trade & Dividend CRUD Cycle', async ({ request }) => {
    // 1. Reset portfolio to $100k
    const resetRes = await request.post('/api/portfolio/reset', {
      data: { initial_cash: 100000.0 },
    });
    expect(resetRes.status()).toBe(200);
    const resetData = await resetRes.json();
    expect(resetData.cash_balance).toBe(100000.0);

    // 2. Deposit Cash $10,000
    const depRes = await request.post('/api/portfolio/deposit', {
      data: { amount: 10000.0, notes: 'E2E Deposit Test' },
    });
    expect(depRes.status()).toBe(200);
    const depData = await depRes.json();
    expect(depData.cash_balance).toBe(110000.0);

    // 3. Withdraw Cash $5,000
    const withRes = await request.post('/api/portfolio/withdraw', {
      data: { amount: 5000.0, notes: 'E2E Withdraw Test' },
    });
    expect(withRes.status()).toBe(200);
    const withData = await withRes.json();
    expect(withData.cash_balance).toBe(105000.0);

    // 4. Direct Buy Trade (10 MSFT @ 400.0)
    const buyRes = await request.post('/api/portfolio/trade', {
      data: { action: 'BUY', ticker: 'MSFT', quantity: 10.0, price: 400.0 },
    });
    expect(buyRes.status()).toBe(200);
    const buyData = await buyRes.json();
    expect(buyData.status).toBe('success');
    expect(buyData.cash_remaining).toBe(105000.0 - 4000.0);

    // 5. Dividend Distribution ($2.50 per share on 10 MSFT = $25.00)
    const divRes = await request.post('/api/portfolio/dividend', {
      data: { ticker: 'MSFT', amount_per_share: 2.50 },
    });
    expect(divRes.status()).toBe(200);
    const divData = await divRes.json();
    expect(divData.total_dividend).toBe(25.0);
    expect(divData.cash_balance).toBe(101000.0 + 25.0);

    // 6. Direct Sell Trade (5 MSFT @ 420.0) -> Realized Gain ($420 - $400) * 5 = $100.00
    const sellRes = await request.post('/api/portfolio/trade', {
      data: { action: 'SELL', ticker: 'MSFT', quantity: 5.0, price: 420.0 },
    });
    expect(sellRes.status()).toBe(200);
    const sellData = await sellRes.json();
    expect(sellData.status).toBe('success');
    expect(sellData.realized_pl).toBe(100.0);

    // 7. Verify Portfolio Status
    const statusRes = await request.get('/api/portfolio');
    expect(statusRes.status()).toBe(200);
    const statusData = await statusRes.json();
    expect(statusData.positions.length).toBe(1);
    expect(statusData.positions[0].ticker).toBe('MSFT');
    expect(statusData.positions[0].shares).toBe(5.0);
    expect(statusData.positions[0].cumulative_dividends).toBe(25.0);

    // 8. Verify Transactions History
    const txRes = await request.get('/api/portfolio/transactions');
    expect(txRes.status()).toBe(200);
    const txData = await txRes.json();
    expect(txData.transactions.length).toBeGreaterThanOrEqual(5);
  });

  test('UI E2E - Two-Step Buy Confirmation & Screenshot Capture', async ({ page }) => {
    await page.goto('/');

    // Reset portfolio first via chat or API to guarantee consistent baseline
    const inputArea = page.getByPlaceholder(/Ask research query/i);
    await inputArea.fill('Reset portfolio');
    const sendBtn = page.getByRole('button', { name: /Send query/i });
    await sendBtn.click();
    await expect(page.getByText('Portfolio Reset Complete')).toBeVisible({ timeout: 15000 });

    // Step 1: Prompt Buy order
    await inputArea.fill('Buy 10 shares of NVDA');
    await sendBtn.click();

    // Verify 2-step confirmation prompt appears
    await expect(page.getByText('Trade Order Confirmation Required')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Confirm purchase\? \[Yes \/ No\]/i)).toBeVisible({ timeout: 15000 });

    // Step 2: Confirm order with 'yes'
    await inputArea.fill('Yes, proceed with order');
    await sendBtn.click();

    // Verify trade execution confirmation appears
    await expect(page.getByText('Trade Confirmation & Execution')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Successfully purchased 10 shares of NVDA/i)).toBeVisible({ timeout: 15000 });

    // Step 3: Request portfolio overview in UI and capture screenshot
    await inputArea.fill('View portfolio NAV, current positions, and cash balance');
    await sendBtn.click();

    // Wait until response streaming completes and portfolio markdown is rendered
    await expect(page.getByRole('heading', { name: /Portfolio & Investment Summary/i })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('cell', { name: 'NVDA' })).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole('button', { name: /Export to Obsidian/i }).last()).toBeVisible({ timeout: 15000 });

    // Scroll chat container to bottom so the portfolio summary table is fully visible in screenshot
    await page.locator('.overflow-y-auto').evaluate((el) => {
      el.scrollTop = el.scrollHeight;
    });
    await page.waitForTimeout(300);

    // Capture screenshot into screenshots/phase3-portfolio.png
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, 'phase3-portfolio.png'),
    });
  });

  test('UI E2E - Two-Step Trade Order Cancellation Flow', async ({ page }) => {
    await page.goto('/');

    const inputArea = page.getByPlaceholder(/Ask research query/i);
    const sendBtn = page.getByRole('button', { name: /Send query/i });

    // Initiate Buy order
    await inputArea.fill('Buy 20 shares of AAPL');
    await sendBtn.click();

    await expect(page.getByText('Trade Order Confirmation Required')).toBeVisible({ timeout: 15000 });

    // Cancel order
    await inputArea.fill('No, cancel order');
    await sendBtn.click();

    // Verify cancellation confirmation
    await expect(page.getByText(/has been cancelled/i)).toBeVisible({ timeout: 15000 });
  });

  test('UI E2E - Cash Deposit, Withdrawal, and Transaction History via Chat', async ({ page }) => {
    await page.goto('/');

    const inputArea = page.getByPlaceholder(/Ask research query/i);
    const sendBtn = page.getByRole('button', { name: /Send query/i });

    // Deposit cash
    await inputArea.fill('Deposit $25,000');
    await sendBtn.click();
    await expect(page.getByText('Cash Deposit Successful')).toBeVisible({ timeout: 15000 });

    // Withdraw cash
    await inputArea.fill('Withdraw $5,000');
    await sendBtn.click();
    await expect(page.getByText('Cash Withdrawal Successful')).toBeVisible({ timeout: 15000 });

    // Show transaction history
    await inputArea.fill('Show transaction history');
    await sendBtn.click();
    await expect(page.getByText('Transaction & Audit History')).toBeVisible({ timeout: 15000 });
  });

  test('UI E2E - Trade Validation Guardrails (Private Company & Insufficient Shares)', async ({ page }) => {
    await page.goto('/');

    const inputArea = page.getByPlaceholder(/Ask research query/i);
    const sendBtn = page.getByRole('button', { name: /Send query/i });

    // 1. Private company buy attempt rejected immediately
    await inputArea.fill('Buy 10 shares of SpaceX');
    await sendBtn.click();
    await expect(page.getByText(/SpaceX is a private company/i).first()).toBeVisible({ timeout: 15000 });

    // 2. Selling unowned shares rejected immediately
    await inputArea.fill('Sell 100 shares of TSLA');
    await sendBtn.click();
    await expect(page.getByText(/Trade Validation Failed/i).first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByText(/Insufficient shares/i).first()).toBeVisible({ timeout: 15000 });
  });

});
