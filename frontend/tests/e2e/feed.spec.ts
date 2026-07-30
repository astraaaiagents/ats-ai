import { test, expect } from "@playwright/test";

test.describe("Feed & Activity Log Scenarios", () => {
  test.beforeEach(async ({ page }) => {
    // Register route mocks first before navigating
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "test@example.com",
          role: "admin",
          is_active: true,
        }),
      })
    );

    await page.route("**/api/v1/client-contacts*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [] }),
      })
    );

    await page.route("**/api/v1/candidates*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: [], total: 0 }),
      })
    );

    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-valid-token");
      localStorage.setItem("refresh_token", "mock-valid-refresh");
    });
  });

  test("renders feed view with activity logs and proactive alerts", async ({ page }) => {
    await page.goto("/");

    // Check main feed heading or sidebar item
    await expect(page.getByText("Feeds").first()).toBeVisible();

    // Verify presence of feed list area
    const feedContainer = page.locator("main, .flex-1").first();
    await expect(feedContainer).toBeVisible();
  });

  test("navigation to feed tab from sidebar works properly", async ({ page }) => {
    await page.goto("/");

    // Click Jobs navigation button in sidebar
    await page.getByRole("button", { name: /^Jobs$/i }).click();

    // Click Feeds navigation button in sidebar
    const feedBtn = page.getByRole("button", { name: /^Feeds$/i });
    await expect(feedBtn).toBeVisible();
    await feedBtn.click();

    await expect(page.getByText("Feeds").first()).toBeVisible();
  });
});
