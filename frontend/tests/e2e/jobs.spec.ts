import { test, expect } from "@playwright/test";

test.describe("Jobs & Client Contacts Scenarios", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-valid-token");
      localStorage.setItem("refresh_token", "mock-valid-refresh");
    });
  });

  test("renders jobs view with search inputs and status filter pills", async ({ page }) => {
    // Intercept client contacts API to return mock jobs
    await page.route("**/api/v1/client-contacts*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          data: [
            {
              id: "job-1",
              req_id: "REQ-901",
              organization_name: "Acme AI Corp",
              title: "Senior AI Engineer",
              location: "San Francisco, CA",
              status: "needs_attention",
              domains: ["AI/ML", "Backend"],
              candidate_count: 12,
              pipeline_summary: "3R · 5S · 4I",
              agent_insight: "High fit candidates ready for client review",
            },
          ],
        }),
      });
    });

    await page.goto("/jobs");

    // Check job card rendering
    await expect(page.getByText("Acme AI Corp — Senior AI Engineer")).toBeVisible();
    await expect(page.getByText("REQ-901")).toBeVisible();
    await expect(page.locator("span", { hasText: "Needs Attention" }).first()).toBeVisible();

    // Verify search filters using regex matchers
    const clientSearchInput = page.getByPlaceholder(/Client name/i);
    const roleSearchInput = page.getByPlaceholder(/Role/i);

    await expect(clientSearchInput).toBeVisible();
    await expect(roleSearchInput).toBeVisible();

    // Filter by client search
    await clientSearchInput.fill("Acme");
    await expect(page.getByText("Acme AI Corp — Senior AI Engineer")).toBeVisible();

    // Filter by nonexistent client
    await clientSearchInput.fill("NonExistentCorp123");
    await expect(page.getByText(/No jobs match your filters|No jobs yet/i)).toBeVisible();
  });
});
