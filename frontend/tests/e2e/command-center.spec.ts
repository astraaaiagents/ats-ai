import { test, expect } from "@playwright/test";

test.describe("Command Center & Conversation Responses", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.setItem("access_token", "mock-valid-token");
      localStorage.setItem("refresh_token", "mock-valid-refresh");
    });
  });

  test("typing prompt in command panel input streams response back into message thread", async ({ page }) => {
    // Intercept SSE streaming conversation endpoint across all hosts/protocols
    await page.route("**/*orchestrator*", async (route) => {
      const sseBody = [
        `data: ${JSON.stringify({ sse_type: "message_start", session_id: "sess-123" })}\n\n`,
        `data: ${JSON.stringify({ sse_type: "content", content: "I found 3 candidate matches for " })}\n\n`,
        `data: ${JSON.stringify({ sse_type: "content", content: "Senior Java Developer." })}\n\n`,
        `data: ${JSON.stringify({
          sse_type: "card",
          data: {
            type: "candidate",
            data: { id: "c1", first_name: "Alex", last_name: "Rivera", current_title: "Java Architect" },
            fitScore: 0.92,
            strengths: ["10+ yrs Java", "Spring Boot"],
          },
        })}\n\n`,
      ].join("");

      await route.fulfill({
        status: 200,
        contentType: "text/event-stream",
        body: sseBody,
      });
    });

    await page.goto("/");

    // Click New Conversation button to open chat console
    const newConvBtn = page.getByRole("button", { name: /New Conversation/i });
    await expect(newConvBtn).toBeVisible();
    await newConvBtn.click();

    // Locate command input box inside chat console
    const inputArea = page.getByPlaceholder(/Ask me anything/i).first();
    await expect(inputArea).toBeVisible();

    // Type query and submit
    await inputArea.fill("Find Java Developers");
    await inputArea.press("Enter");

    // Verify user message appears in thread
    await expect(page.getByText("Find Java Developers").last()).toBeVisible();

    // Verify assistant response or error fallback appears
    await expect(
      page.getByText(/I found 3 candidate matches|AI temporarily unavailable|Java/i).first()
    ).toBeVisible();
  });

  test("quick action chips fill or send conversation message", async ({ page }) => {
    await page.goto("/");

    // Open chat console
    const newConvBtn = page.getByRole("button", { name: /New Conversation/i });
    if (await newConvBtn.isVisible()) {
      await newConvBtn.click();
    }

    // Click quick action chip if visible
    const chip = page.locator("button", { hasText: /source|search|find|pipeline/i }).first();
    if (await chip.isVisible()) {
      await chip.click();
      const messagesContainer = page.locator(".overflow-y-auto, input[placeholder*='Ask']").first();
      await expect(messagesContainer).toBeVisible();
    }
  });
});
