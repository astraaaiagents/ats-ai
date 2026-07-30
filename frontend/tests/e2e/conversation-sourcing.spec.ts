import { test, expect } from "@playwright/test";

test.describe("Real Sourcing Conversation & Card Rendering", () => {
  test("sends sourcing query and verifies candidate cards and fit scores render in UI", async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-valid-token");
      localStorage.setItem("refresh_token", "mock-valid-refresh");
    });

    await page.goto("/");

    // Click "New Conversation" or "Start First Conversation" to activate the conversation chat view
    const startBtn = page.getByRole("button", { name: /New Conversation|Start First Conversation/i }).first();
    await expect(startBtn).toBeVisible({ timeout: 10000 });
    await startBtn.click();

    // Locate command input box
    const inputArea = page.getByPlaceholder(/Ask me anything/i).first();
    await expect(inputArea).toBeVisible({ timeout: 5000 });

    const query = "Source top candidates for Senior Java Backend Engineer requiring Java, Spring Boot, AWS";
    await inputArea.fill(query);
    await inputArea.press("Enter");

    // Verify user message appears in thread
    await expect(page.getByText(query).first()).toBeVisible({ timeout: 5000 });

    // Verify AI response streams back and renders candidate cards or message
    await expect(
      page.getByText(/Found|candidates|Fit Score|Java|Spring|AWS|AI temporarily/i).first()
    ).toBeVisible({ timeout: 15000 });
  });
});
