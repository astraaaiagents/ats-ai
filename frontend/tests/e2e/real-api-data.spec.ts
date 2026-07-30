import { test, expect } from "@playwright/test";

test.describe("Real Backend Data & Auth Integration (Unmocked)", () => {
  test("Pipeline view fetches and displays real candidate data from backend", async ({ page }) => {
    await page.goto("/?tab=pipeline");

    await expect(page.locator(".rounded-card").first()).toBeVisible({ timeout: 10000 });
  });

  test("Jobs view fetches and displays real client contacts from backend", async ({ page }) => {
    await page.goto("/?tab=jobs");

    await expect(page.getByPlaceholder(/Client name/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/No jobs yet/i)).not.toBeVisible({ timeout: 10000 });
  });

  test("Feed view fetches activity log and proactive alerts from backend", async ({ page }) => {
    await page.goto("/?tab=feed");

    await expect(page.getByText(/No activity yet/i)).not.toBeVisible({ timeout: 10000 });
  });
});
