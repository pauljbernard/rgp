import { expect, test } from "@playwright/test";
import { loginAsPlatformAdmin, loginAsReviewer } from "./helpers";

test.describe("Admin browser journeys", () => {
  test("template catalog drills into the dedicated version workbench", async ({ page }) => {
    await loginAsPlatformAdmin(page);
    await page.goto("/admin/templates");

    await expect(page.getByRole("heading", { name: "Admin Templates" })).toBeVisible();
    await expect(page.getByText("Catalog Summary")).toBeVisible();
    await expect(page.getByRole("link", { name: "Assessment Revision" }).first()).toBeVisible();

    await page.getByRole("link", { name: "Assessment Revision" }).first().click();

    await page.waitForURL(/\/admin\/templates\/.+\/.+/);
    await expect(page.getByText("Definition Editor")).toBeVisible();
    await expect(page.getByText("Version Comparison")).toBeVisible();
    await expect(page.getByText("Catalog Summary")).toHaveCount(0);
  });

  test("non-admin access to template admin is handled as forbidden instead of crashing", async ({ page }) => {
    await loginAsReviewer(page);
    await page.goto("/admin/templates");

    await expect(page.getByRole("heading", { name: "Access Restricted" })).toBeVisible();
    await expect(page.getByText("This route requires additional permissions.")).toBeVisible();
    await expect(page.getByText("/api/v1/admin/templates")).toBeVisible();
  });
});
