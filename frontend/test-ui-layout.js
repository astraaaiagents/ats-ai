/* eslint-disable @typescript-eslint/no-require-imports */
/* ── UI Layout Test ────────────────────────────────────────────────

   Verifies:
   1. Chat area fills remaining space when sidebar is open (layoutWidth - sidebarWidth)
   2. Chat area fills full screen when sidebar is collapsed
*/

const { chromium } = require("playwright");

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // Collect console logs
  page.on("console", (msg) => {
    if (msg.type() === "error") console.log(`[BROWSER ERROR] ${msg.text()}`);
  });

  // Clear localStorage before any page loads
  await page.addInitScript(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  // Navigate to the login page
  await page.goto("http://localhost:3000/login", { waitUntil: "networkidle", timeout: 15000 });

  // Wait for the login form to load
  await page.waitForSelector('input[type="email"]', { timeout: 10000 });
  await page.waitForTimeout(1000);

  // Fill in the login form with recruiter credentials (org-level user)
  await page.fill('input[type="email"]', "recruiter@example.com");
  await page.fill('input[type="password"]', "recruiter123");

  // Submit the form
  await page.click('button[type="submit"]');

  // Wait for navigation to main app
  await page.waitForURL("**/*", { timeout: 10000 });

  // Wait for React to hydrate
  await page.waitForTimeout(3000);

  // Get the layout dimensions
  const layout = await page.locator("div.flex.h-screen.w-full.overflow-hidden");
  const layoutCount = await layout.count();

  if (layoutCount === 0) {
    console.log("❌ Layout not found - page might not be rendered yet");
    await page.screenshot({ path: "test-ui-layout.png", fullPage: true });
    await browser.close();
    process.exit(1);
  }

  const layoutBox = await layout.first().boundingBox();
  console.log("Layout dimensions:");
  console.log(`  Width: ${layoutBox.width}px`);
  console.log(`  Height: ${layoutBox.height}px`);

  // Get the sidebar dimensions
  const sidebar = await page.locator("aside.flex.h-full.w-\\[280px\\].shrink-0.flex-col.border-r.border-border.bg-surface");
  const sidebarCount = await sidebar.count();

  let sidebarWidth = 0;
  if (sidebarCount > 0) {
    const sidebarBox = await sidebar.first().boundingBox();
    sidebarWidth = sidebarBox.width;
    console.log("\nSidebar dimensions:");
    console.log(`  Width: ${sidebarWidth}px`);
    console.log(`  Height: ${sidebarBox.height}px`);
    console.log(`  X: ${sidebarBox.x}px`);
  } else {
    console.log("\nSidebar not found (collapsed)");
  }

  // Get the chat area dimensions
  const chatArea = await page.locator("div.relative.flex.min-w-0.flex-1.flex-col.overflow-hidden");
  const chatAreaCount = await chatArea.count();

  if (chatAreaCount === 0) {
    console.log("\n❌ Chat area not found");
    await page.screenshot({ path: "test-ui-layout.png", fullPage: true });
    await browser.close();
    process.exit(1);
  }

  const chatAreaBox = await chatArea.first().boundingBox();
  console.log("\nChat area dimensions:");
  console.log(`  Width: ${chatAreaBox.width}px`);
  console.log(`  Height: ${chatAreaBox.height}px`);
  console.log(`  X: ${chatAreaBox.x}px`);
  console.log(`  Right edge: ${chatAreaBox.x + chatAreaBox.width}px`);

  // Verify: chat area should fill remaining space (layoutWidth - sidebarWidth)
  const expectedChatWidth = layoutBox.width - sidebarWidth;
  const chatFillsCorrectly = Math.abs(chatAreaBox.width - expectedChatWidth) < 5; // 5px tolerance

  console.log(`\nExpected chat width (with sidebar ${sidebarWidth}px): ${expectedChatWidth}px`);
  console.log(`Actual chat width: ${chatAreaBox.width}px`);

  if (chatFillsCorrectly) {
    console.log("✅ Chat area fills remaining space correctly");
  } else {
    console.log("❌ Chat area does NOT fill remaining space");
  }

  // Verify: chat area right edge should match layout right edge
  const rightEdgeMatches = Math.abs((chatAreaBox.x + chatAreaBox.width) - layoutBox.width) < 5;
  if (rightEdgeMatches) {
    console.log("✅ Chat area right edge matches layout right edge");
  } else {
    console.log(`❌ Chat area right edge (${chatAreaBox.x + chatAreaBox.width}) does not match layout (${layoutBox.width})`);
  }

  // Verify: chat area height should match layout height
  const heightMatches = Math.abs(chatAreaBox.height - layoutBox.height) < 5;
  if (heightMatches) {
    console.log("✅ Chat area height matches layout height");
  } else {
    console.log(`❌ Chat area height (${chatAreaBox.height}) does not match layout (${layoutBox.height})`);
  }

  // Now test: collapse sidebar and verify chat fills full screen
  console.log("\n--- Collapsing sidebar ---");

  // Click the toggle button (collapse sidebar)
  await page.getByRole("button", { name: "Collapse sidebar" }).click();

  // Wait for animation
  await page.waitForTimeout(500);

  // Check sidebar is gone
  const sidebarAfter = await page.locator("aside.flex.h-full.w-\\[280px\\].shrink-0.flex-col.border-r.border-border.bg-surface");
  const sidebarAfterCount = await sidebarAfter.count();

  console.log(`Sidebar visible after collapse: ${sidebarAfterCount > 0}`);

  // Get chat area after collapse
  const chatAreaAfter = await page.locator("div.relative.flex.min-w-0.flex-1.flex-col.overflow-hidden");
  const chatAreaAfterBox = await chatAreaAfter.first().boundingBox();

  console.log("\nAfter sidebar collapse:");
  console.log(`  Chat width: ${chatAreaAfterBox.width}px`);
  console.log(`  Chat X: ${chatAreaAfterBox.x}px`);
  console.log(`  Chat right edge: ${chatAreaAfterBox.x + chatAreaAfterBox.width}px`);

  const fillsFullScreen = Math.abs(chatAreaAfterBox.width - layoutBox.width) < 5 &&
                          Math.abs(chatAreaAfterBox.x) < 5;

  if (sidebarAfterCount === 0 && fillsFullScreen) {
    console.log("✅ Sidebar collapsed, chat fills full screen");
  } else if (sidebarAfterCount > 0) {
    console.log("⚠️ Sidebar still visible after collapse");
  } else {
    console.log("⚠️ Chat does not fill full screen after collapse");
  }

  // Take a screenshot
  await page.screenshot({ path: "test-ui-layout.png", fullPage: true });
  console.log("\nScreenshot saved to test-ui-layout.png");

  await browser.close();
})();
