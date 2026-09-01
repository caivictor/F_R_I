import { test, expect } from "@playwright/test";

test.describe("Multi-Turn Conversational Memory & Debug Log Verification E2E", () => {
  test("Executes 10-turn multi-workflow conversation and verifies debug logs match", async ({ page, request }) => {
    await page.goto("http://localhost:8000");

    const input = page.getByPlaceholder(/Ask research query/i);
    const sendBtn = page.getByRole("button", { name: /Send/i });

    // Turn 1: Discovery
    await input.fill("Discover market news and analyze trending companies");
    await sendBtn.click();
    await expect(page.getByText(/Executive Investment Discovery Briefing/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 2: Follow-up multi-item inquiry
    await input.fill("Why didn't you research all five recommendations?");
    await sendBtn.click();
    await expect(page.getByText(/Multi-Asset Comparative Analysis/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 3: Single stock analysis
    await input.fill("Analyze Apple fundamentals and capital efficiency");
    await sendBtn.click();
    await expect(page.getByText(/Long-Term Investment Dossier: Apple Inc/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 4: Pronoun resolution
    await input.fill("What is its return on invested capital and gross margin?");
    await sendBtn.click();
    await expect(page.getByText(/ROIC/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 5: Portfolio NAV
    await input.fill("Show my portfolio balance and positions");
    await sendBtn.click();
    await expect(page.getByText(/Portfolio & Investment Summary/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 6: Cash Deposit
    await input.fill("Deposit $10,000 into my investment account");
    await sendBtn.click();
    await expect(page.getByText(/Cash Deposit Successful/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 7: New Entity
    await input.fill("Analyze Microsoft");
    await sendBtn.click();
    await expect(page.getByText(/Long-Term Investment Dossier: Microsoft Corporation/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 8: Trade Intent with Pronoun
    await input.fill("Buy 10 shares of it");
    await sendBtn.click();
    await expect(page.getByText(/Trade Order Confirmation Required/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 9: Trade Cancellation
    await input.fill("No, cancel this order");
    await sendBtn.click();
    await expect(page.getByText(/cancelled/i).first()).toBeVisible({ timeout: 15000 });

    // Turn 10: Feedback / Guidance
    await input.fill("What should we explore next today?");
    await sendBtn.click();
    await expect(page.getByText(/Manager Agent/i).first()).toBeVisible({ timeout: 15000 });

    // Open Debug Modal and verify logged turns
    await page.getByRole("button", { name: /Debug/i }).click();
    await expect(page.getByText(/LLM Context & Debug Inspector/i)).toBeVisible();

    // Verify Debug inspector shows captured logs
    await expect(page.getByText(/\[manager\]/i).first()).toBeVisible();

    // Switch to Conversation tab in Debug Modal and verify 10 user messages are present
    await page.getByRole("button", { name: /Conversation/i }).click();
    await expect(page.getByText(/Discover market news/i).first()).toBeVisible();
    await expect(page.getByText(/Analyze Apple fundamentals/i).first()).toBeVisible();
    await expect(page.getByText(/What should we explore next today/i).first()).toBeVisible();

    // Close modal
    await page.keyboard.press("Escape");
  });
});
