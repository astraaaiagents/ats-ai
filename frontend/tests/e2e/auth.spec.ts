import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  test("login page renders correctly with all elements", async ({ page }) => {
    await page.goto("/login");

    // Title & branding
    await expect(page).toHaveTitle(/ATS/i);
    await expect(page.getByText(/ATS Agent/i)).toBeVisible();
    await expect(page.getByText(/Sign in to your account/i)).toBeVisible();

    // Inputs
    await expect(page.getByLabel(/Email/i)).toBeVisible();
    await expect(page.getByLabel(/Password/i)).toBeVisible();

    // Submit button
    await expect(page.getByRole("button", { name: /Sign in/i })).toBeVisible();
  });

  test("shows HTML5 validation error on empty submit", async ({ page }) => {
    await page.goto("/login");

    const emailInput = page.getByLabel(/Email/i);
    await expect(emailInput).toHaveAttribute("required", "");

    // Click submit with empty inputs
    await page.getByRole("button", { name: /Sign in/i }).click();

    // Verify invalid state on email
    const isValid = await emailInput.evaluate((el: HTMLInputElement) => el.checkValidity());
    expect(isValid).toBe(false);
  });

  test("mock token login redirects to dashboard", async ({ page }) => {
    await page.goto("/login");

    // Inject mock local storage token
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-jwt-token");
      localStorage.setItem("refresh_token", "mock-refresh-token");
    });

    await page.goto("/");
    await expect(page).not.toHaveURL(/\/login/);
  });
});
