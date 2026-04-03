import { expect, type APIRequestContext, type Page } from "@playwright/test";

const apiBaseUrl = process.env.RGP_API_BASE ?? "http://127.0.0.1:8001";

export async function loginAsPlatformAdmin(page: Page) {
  await page.goto("/login");
  await page.getByRole("link", { name: "Platform Admin" }).click();
  await page.waitForURL("**/requests");
  await expect(page.getByRole("heading", { name: "Requests" })).toBeVisible();
}

export async function issueDevToken(request: APIRequestContext) {
  const response = await request.post(`${apiBaseUrl}/api/v1/auth/dev-token`, {
    data: {
      user_id: "user_demo",
      tenant_id: "tenant_demo",
      roles: ["admin", "operator", "reviewer", "submitter"],
      expires_in_seconds: 3600,
    },
  });
  expect(response.ok()).toBeTruthy();
  const payload = (await response.json()) as { access_token: string };
  return payload.access_token;
}

export async function createSubmittedAssessmentRequest(
  request: APIRequestContext,
  title: string,
  assessmentId: string,
) {
  const token = await issueDevToken(request);
  let created: { id: string } | null = null;

  for (let attempt = 0; attempt < 3; attempt += 1) {
    const createResponse = await request.post(`${apiBaseUrl}/api/v1/requests`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      data: {
        template_id: "tmpl_assessment",
        template_version: "1.4.0",
        title: `${title} ${attempt ? `retry-${attempt}` : ""}`.trim(),
        summary: "Browser journey setup request.",
        priority: "medium",
        input_payload: {
          assessment_id: `${assessmentId}_${attempt}`,
          revision_reason: "Standards alignment",
          target_window: "Spring 2026",
        },
      },
    });
    if (createResponse.status() === 201) {
      created = (await createResponse.json()) as { id: string };
      break;
    }
    expect(createResponse.status()).toBe(409);
  }

  expect(created).not.toBeNull();

  const submitResponse = await request.post(`${apiBaseUrl}/api/v1/requests/${created!.id}/submit`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    data: {},
  });
  expect(submitResponse.ok()).toBeTruthy();

  return created!.id;
}

export async function waitForRequestInQueue(request: APIRequestContext, requestId: string) {
  const token = await issueDevToken(request);
  const deadline = Date.now() + 30_000;

  while (Date.now() < deadline) {
    const response = await request.get(`${apiBaseUrl}/api/v1/requests?request_id=${requestId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (response.ok()) {
      const payload = (await response.json()) as { items: Array<{ id: string }> };
      if (payload.items.some((item) => item.id === requestId)) {
        return;
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 1_000));
  }

  throw new Error(`Request ${requestId} did not appear in the queue API in time.`);
}
