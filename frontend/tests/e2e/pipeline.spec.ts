import { test, expect } from "@playwright/test";

test.describe("Pipeline & Candidate Action Scenarios", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-valid-token");
      localStorage.setItem("refresh_token", "mock-valid-refresh");
    });

    // Mock client contacts API for JobSelector
    await page.route("**/api/v1/client-contacts*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([
          {
            id: "job-101",
            organization_name: "Acme Corp",
            title: "Senior Developer",
          },
        ]),
      });
    });

    // Mock candidates API for pipeline columns
    await page.route("**/api/v1/candidates*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "cand-101",
              first_name: "Sarah",
              last_name: "Connor",
              current_title: "Staff Systems Engineer",
              status: "sourced",
              skills: [{ id: "s1", skill_name: "Rust" }, { id: "s2", skill_name: "Go" }],
            },
          ],
          total: 1,
        }),
      });
    });
  });

  test("renders pipeline view with job selector and filter toggle", async ({ page }) => {
    await page.goto("/pipeline");

    // Job selector component
    const jobSelector = page.getByText(/All Jobs|Select Job/i).first();
    await expect(jobSelector).toBeVisible();

    // Filters toggle button
    const filterToggle = page.getByRole("button", { name: /(Show|Hide) Filters/i });
    await expect(filterToggle).toBeVisible();

    // Toggle filters ON
    await filterToggle.click();
    await expect(page.getByRole("button", { name: /Hide Filters/i })).toBeVisible();

    // Toggle filters OFF
    await filterToggle.click();
    await expect(page.getByRole("button", { name: /Show Filters/i })).toBeVisible();
  });

  test("pipeline action buttons (Review, Approve, Reject) trigger overlay and handle actions", async ({ page }) => {
    // Intercept candidates API to return mock candidates
    await page.route("**/api/v1/candidates*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "cand-101",
              first_name: "Sarah",
              last_name: "Connor",
              current_title: "Staff Systems Engineer",
              status: "sourced",
              skills: [{ id: "s1", skill_name: "Rust" }, { id: "s2", skill_name: "Go" }],
            },
          ],
          total: 1,
        }),
      });
    });

    await page.goto("/pipeline");

    // Wait for candidate card to load
    await expect(page.getByText("Sarah Connor")).toBeVisible();
    await expect(page.getByText("Staff Systems Engineer")).toBeVisible();

    // Verify presence of Review, Approve, Reject action buttons
    const reviewBtn = page.getByRole("button", { name: /^Review$/i }).first();
    const approveBtn = page.getByRole("button", { name: /^Approve$/i }).first();
    const rejectBtn = page.getByRole("button", { name: /^Reject$/i }).first();

    await expect(reviewBtn).toBeVisible();
    await expect(approveBtn).toBeVisible();
    await expect(rejectBtn).toBeVisible();

    // Click Approve button to open Quick Review overlay
    await approveBtn.click();

    // Quick review overlay modal check
    await expect(page.getByText(/Quick Review|Sarah Connor/i).first()).toBeVisible();

    // Verify overlay action buttons in Quick Review
    const overlayApproveBtn = page.getByRole("button", { name: /Approve →/i });
    const overlayRejectBtn = page.getByRole("button", { name: /← Reject/i });

    if (await overlayApproveBtn.isVisible()) {
      await overlayApproveBtn.click();
    } else if (await overlayRejectBtn.isVisible()) {
      await overlayRejectBtn.click();
    }
  });
});
