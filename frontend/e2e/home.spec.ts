import { test, expect } from "@playwright/test";

test.describe("home smoke", () => {
  test("loads / and renders the blog layout", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveTitle(/Blogger Agent/);
    await expect(
      page.getByRole("heading", { level: 1, name: "Blog" })
    ).toBeVisible();
    await expect(page.locator("header")).toBeVisible();
    await expect(page.locator("footer")).toBeVisible();
  });
});