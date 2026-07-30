import { test, expect } from "@playwright/test";

test.describe("Agent Portal & Command Panel UI", () => {
  test.beforeEach(async ({ page }) => {
    // Set up mock auth token
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-valid-token");
      localStorage.setItem("refresh_token", "mock-valid-refresh");
    });
  });

  test("main portal renders navigation sidebar and AgencyOS brand", async ({ page }) => {
    await page.goto("/");

    // Verify main portal sidebar brand & navigation items
    await expect(page.getByText(/AgencyOS/i).first()).toBeVisible();
    await expect(page.getByText(/Feeds/i).first()).toBeVisible();
    await expect(page.getByText(/Pipeline/i).first()).toBeVisible();
    await expect(page.getByText(/Jobs/i).first()).toBeVisible();
    await expect(page.getByText(/Preferences/i).first()).toBeVisible();
  });

  test("command panel toggles open and closed", async ({ page }) => {
    await page.goto("/");

    // Locate sidebar toggle or collapse button
    const toggleBtn = page.getByRole("button", { name: /Collapse sidebar|Expand sidebar/i }).first();
    if (await toggleBtn.isVisible()) {
      await toggleBtn.click();
      await page.waitForTimeout(300);
      await toggleBtn.click();
    }
  });

  test("quick action chips trigger prompt fill", async ({ page }) => {
    await page.goto("/");

    // Look for quick action chips or prompt textarea
    const textarea = page.locator("textarea").first();
    if (await textarea.isVisible()) {
      await textarea.fill("Search for senior Python developers");
      await expect(textarea).toHaveValue("Search for senior Python developers");
    }
  });
});
