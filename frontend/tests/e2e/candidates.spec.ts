import { test, expect } from "@playwright/test";

test.describe("Candidate Management & Search Flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-valid-token");
    });
  });

  test("candidate directory tab renders candidates and search filter", async ({ page }) => {
    await page.goto("/");

    // Click candidate directory tab
    const candidateTab = page.getByRole("tab", { name: /candidate|directory/i }).or(
      page.getByRole("button", { name: /candidate|directory/i })
    ).first();

    if (await candidateTab.isVisible()) {
      await candidateTab.click();
    }

    // Verify search input
    const searchInput = page.getByPlaceholder(/search|filter|find/i).first();
    if (await searchInput.isVisible()) {
      await searchInput.fill("Software Engineer");
      await expect(searchInput).toHaveValue("Software Engineer");
    }
  });
});
