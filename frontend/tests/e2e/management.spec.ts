import { test, expect } from "@playwright/test";

test.describe("Candidate & Job Management Creation & Movement", () => {
  test.beforeEach(async ({ page }) => {
    // Set authenticated localStorage token
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-access-token");
      localStorage.setItem("refresh_token", "mock-refresh-token");
    });

    // Intercept auth checks
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "00000000-0000-0000-0000-000000000001",
          email: "test@example.com",
          role: "admin",
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      })
    );

    await page.route("**/api/v1/candidates*", (route, request) => {
      if (request.method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [
              {
                id: "cand-123",
                first_name: "Alice",
                last_name: "Smith",
                email: "alice@example.com",
                current_title: "Senior Developer",
                status: "sourced",
                skills: [{ id: "1", skill_name: "React", proficiency: 5, years_experience: 4 }],
                documents: [],
                timeline: [],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
            pagination: { next_cursor: null, has_more: false, total: 1, sort: null },
          }),
        });
      }
      if (request.method() === "POST") {
        return route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "cand-999",
            first_name: "John",
            last_name: "Doe",
            email: "john.doe@example.com",
            current_title: "Staff Architect",
            status: "sourced",
            skills: [],
            documents: [],
            timeline: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
      }
      if (request.method() === "PATCH") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "cand-123",
            first_name: "Alice",
            last_name: "Smith",
            status: "reviewing",
          }),
        });
      }
      return route.continue();
    });

    await page.route("**/api/v1/client-contacts*", (route, request) => {
      if (request.method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: [
              {
                id: "job-101",
                organization_name: "TechCorp",
                title: "Frontend Engineer",
                location: "San Francisco, CA",
                status: "healthy",
              },
            ],
            pagination: { next_cursor: null, has_more: false, total: 1, sort: null },
          }),
        });
      }
      if (request.method() === "POST") {
        return route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: "job-202",
            organization_name: "Showcase Inc",
            title: "Lead AI Engineer",
            email: "hiring@showcase.ai",
            location: "Remote",
            status: "healthy",
          }),
        });
      }
      return route.continue();
    });
  });

  test("creates a new candidate from pipeline view modal", async ({ page }) => {
    await page.goto("/pipeline");

    const newCandBtn = page.getByRole("button", { name: /New Candidate/i });
    await expect(newCandBtn).toBeVisible();
    await newCandBtn.click();

    await expect(page.locator("h3", { hasText: "Create New Candidate" })).toBeVisible();

    await page.fill("input[placeholder='Jane']", "John");
    await page.fill("input[placeholder='Doe']", "Doe");
    await page.fill("input[placeholder='jane.doe@example.com']", "john.doe@example.com");
    await page.fill("input[placeholder='Senior Frontend Developer']", "Staff Architect");

    await page.click("button:has-text('Create Candidate')");
    await expect(page.locator("h3", { hasText: "Create New Candidate" })).not.toBeVisible();
  });

  test("moves candidate stage using stage selector in pipeline card", async ({ page }) => {
    await page.goto("/pipeline");

    const stageSelect = page.locator("select").first();
    await expect(stageSelect).toBeVisible();
    await stageSelect.selectOption("in_review");
  });

  test("creates a new job posting from jobs view modal", async ({ page }) => {
    await page.goto("/jobs");

    await page.click("button:has-text('New Job')");
    await expect(page.locator("h3", { hasText: "Create New Job Posting" })).toBeVisible();

    await page.fill("input[placeholder='Acme AI Corp']", "Showcase Inc");
    await page.fill("input[placeholder='Lead Backend Engineer']", "Lead AI Engineer");
    await page.fill("input[placeholder='hiring@acme.ai']", "hiring@showcase.ai");

    await page.click("button:has-text('Create Job Posting')");
    await expect(page.locator("h3", { hasText: "Create New Job Posting" })).not.toBeVisible();
  });
});
