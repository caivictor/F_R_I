import { test, expect } from "@playwright/test";

test.describe("Sessions Continuity & Security Audit E2E", () => {
  test("Session History Modal Workflow & Memory Continuity", async ({ page }) => {
    await page.goto("http://localhost:8000");

    // Check Header has History and Security buttons
    await expect(page.getByRole("button", { name: /History/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Security/i })).toBeVisible();

    // Open History Modal
    await page.getByRole("button", { name: /History/i }).click();
    await expect(page.getByText(/Chat History & Context Memory/i)).toBeVisible();

    // Close Modal
    await page.keyboard.press("Escape");

    // Open Security Modal
    await page.getByRole("button", { name: /Security/i }).click();
    await expect(page.getByText(/Security Agent Posture Audit/i)).toBeVisible();
    await expect(page.getByText(/SEC-001/i)).toBeVisible();
  });
});
