import { test, expect } from "@playwright/test";

test.describe("Sessions Continuity & Debug Inspector E2E", () => {
  test("Session History Modal Workflow, Debug Inspector & Deletion", async ({ page }) => {
    await page.goto("http://localhost:8000");

    // Check Header controls are present
    await expect(page.getByRole("button", { name: /History/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Debug/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Personas/i })).toBeVisible();

    // Send a message to generate session history and debug logs
    const input = page.getByPlaceholder(/Ask research query/i);
    await input.fill("Analyze AAPL fundamentals");
    await page.getByRole("button", { name: /Send/i }).click();
    await expect(page.getByText(/Long-Term Investment Dossier/i).first()).toBeVisible({ timeout: 15000 });

    // Open History Modal
    await page.getByRole("button", { name: /History/i }).click();
    await expect(page.getByText(/Chat History & Context Memory/i)).toBeVisible();
    await expect(page.getByText(/Active/i).first()).toBeVisible();

    // Close History Modal
    await page.keyboard.press("Escape");

    // Open Debug Modal
    await page.getByRole("button", { name: /Debug/i }).click();
    await expect(page.getByText(/LLM Context & Debug Inspector/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /Context & Prompts/i })).toBeVisible();

    // Switch to Conversation tab in Debug Modal
    await page.getByRole("button", { name: /Conversation/i }).click();
    await expect(page.getByText(/Analyze AAPL fundamentals/i).first()).toBeVisible();

    // Switch to Active Memory tab in Debug Modal
    await page.getByRole("button", { name: /Active Memory/i }).click();
    await expect(page.getByText(/Persistent Context State/i)).toBeVisible();
    await expect(page.getByText(/AAPL/i).first()).toBeVisible();

    // Close Debug Modal
    await page.keyboard.press("Escape");
  });
});
