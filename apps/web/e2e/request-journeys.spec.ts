import { expect, test } from "@playwright/test";
import { createSubmittedAssessmentRequest, loginAsPlatformAdmin, waitForRequestInQueue } from "./helpers";

function uniqueSuffix() {
  return `${Date.now()}-${Math.floor(Math.random() * 10_000)}`;
}

test.describe("Request browser journeys", () => {
  test("submitter can create a request, submit it, and drill back into it from the queue", async ({ page, request }) => {
    const suffix = uniqueSuffix();
    const title = `Browser Journey ${suffix}`;

    await loginAsPlatformAdmin(page);
    await page.goto("/requests/new");
    await expect(page.getByRole("heading", { name: "Select Request Template" })).toBeVisible();
    await page.getByRole("link", { name: /Assessment Revision/i }).click();

    await page.getByLabel("Title").fill(title);
    await page.getByLabel("Summary").fill("Validate browser request creation and drill-down.");
    await page.getByLabel("Assessment ID *").fill(`asm_browser_${suffix}`);
    await page.getByLabel("Revision Reason *").selectOption("Standards alignment");
    await page.getByLabel("Target Window").fill("Spring 2026");
    await page.getByRole("button", { name: "Create Draft" }).click();

    await page.waitForURL(/\/requests\/req_/);
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.getByText("draft").first()).toBeVisible();

    const requestUrl = page.url();
    const requestId = requestUrl.split("/requests/")[1];
    await page.getByRole("button", { name: "Submit Request" }).click();
    await expect(page.getByText("submitted").first()).toBeVisible();

    await waitForRequestInQueue(request, requestId);
    await page.goto(`/requests?request_id=${requestId}`);
    const requestRow = page.locator("tr").filter({ hasText: requestId }).first();
    await expect(requestRow).toBeVisible({ timeout: 30_000 });
    await requestRow.getByRole("link", { name: title }).click();
    await page.waitForURL(`**/requests/${requestId}`);
    await expect(page.getByRole("heading", { name: title })).toBeVisible();
    await expect(page.getByText("submitted").first()).toBeVisible();
  });

  test("operator can assign a request to Codex and observe live session output", async ({ page, request }) => {
    test.slow();
    const suffix = uniqueSuffix();
    const requestId = await createSubmittedAssessmentRequest(
      request,
      `Agent Browser Journey ${suffix}`,
      `asm_agent_browser_${suffix}`,
    );

    await loginAsPlatformAdmin(page);
    await page.goto(`/requests/${requestId}/agents`);

    await expect(page.getByRole("heading", { name: "Request Agents" })).toBeVisible();
    await page.getByLabel("Agent Integration").selectOption("int_agent_codex");
    await page.getByLabel("Agent Label").fill(`Codex ${suffix}`);
    await page.getByLabel("Initial Prompt").fill(
      "Provide a concise revision plan with one summary, two changes, and one reviewer risk.",
    );
    await page.getByRole("button", { name: "Assign Agent Session" }).click();

    await page.waitForURL(new RegExp(`/requests/${requestId}/agents/ags_`));
    await expect(page.getByText("Current State")).toBeVisible();
    await expect(page.getByText("Current Agent Response")).toBeVisible();
    await expect(page.getByText(/\*\*Summary:\*\*/).first()).toBeVisible({ timeout: 90_000 });
    await expect(page.getByText(/received your guidance/i)).not.toBeVisible();
    await expect(page.getByText("Latest Agent Response")).toBeVisible();
    await expect(page.getByText("Session State")).toBeVisible();
    await expect(page.getByText("Messages: 2")).toBeVisible();
  });
});
