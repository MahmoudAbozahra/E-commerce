import { expect, test } from "@playwright/test";

async function expectLoadedProductImages(page: import("@playwright/test").Page, minimum = 1) {
  const images = page.locator("img[data-product-image]");
  await expect(images.first()).toBeVisible();
  expect(await images.count()).toBeGreaterThanOrEqual(minimum);
  for (let index = 0; index < minimum; index += 1) {
    const image = images.nth(index);
    await image.scrollIntoViewIfNeeded();
    await expect.poll(async () => image.evaluate((node) => (node as HTMLImageElement).complete && (node as HTMLImageElement).naturalWidth > 0)).toBe(true);
  }
  await expect(page.locator("[data-image-fallback]")).toHaveCount(0);
}

test("server-rendered rail opens and reverses to the collection", async ({ page }) => {
  const response = await page.goto("/");
  expect(response?.ok()).toBeTruthy();
  await expect(page.getByRole("heading", { name: /choose the piece/i })).toBeVisible();
  await expectLoadedProductImages(page, 8);
  await expect(page.getByText("6 / 10", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Next product", exact: true }).first().click();
  await expect(page.getByText("7 / 10", { exact: true })).toBeVisible();
  const product = page.getByRole("button", { name: /preview/i }).first();
  await product.focus();
  await product.press("Enter");
  await expect(page.getByRole("dialog")).toBeVisible();
  await expectLoadedProductImages(page, 1);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toBeHidden();
  await expect(product).toBeFocused();
});

test("product images rotate on the same circular interaction", async ({ page }) => {
  await page.goto("/products/olive-weekend-set");
  await expectLoadedProductImages(page, 3);
  await expect(page.getByText("1 / 3", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Next product image" }).click();
  await expect(page.getByText("2 / 3", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Previous product image" }).click();
  await expect(page.getByText("1 / 3", { exact: true })).toBeVisible();
});

test("visual variants and two-image products render as complete inner rings", async ({ page }) => {
  await page.goto("/products/ivory-blazer-set");
  await expectLoadedProductImages(page, 3);
  await expect(page.getByLabel("color options orbit")).toBeVisible();
  await expect(page.getByRole("button", { name: /select color ivory and taupe/i })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Rotate to image 2" })).toHaveCount(2);
  await page.getByRole("button", { name: "Next product image" }).click();
  await expect(page.getByText("2 / 2", { exact: true })).toBeVisible();
});

test("catalog and direct product URLs expose crawlable content", async ({ page }) => {
  await page.goto("/products");
  await expectLoadedProductImages(page, 8);
  const link = page.locator('a[href^="/products/"]').first();
  const name = await link.locator("h2").textContent();
  await link.click();
  await expect(page).toHaveURL(/\/products\//);
  await page.reload();
  await expect(page.getByText(name ?? "", { exact: true }).first()).toBeVisible();
  await expect(page.locator('script[type="application/ld+json"]')).toHaveCount(2);
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", /\/products\//);
  await expectLoadedProductImages(page, 1);
});

test("link CTAs keep the shared primary button contrast", async ({ page }) => {
  await page.goto("/cart");
  const cta = page.getByRole("link", { name: "Sign in to continue" });
  await expect(cta).toBeVisible();
  await expect.poll(() => cta.evaluate((element) => {
    const style = getComputedStyle(element);
    return { color: style.color, background: style.backgroundColor };
  })).toEqual({ color: "rgb(255, 253, 248)", background: "rgb(31, 36, 33)" });
});

test("anonymous session is a normal state rather than an auth error", async ({ request }) => {
  const response = await request.get("/api/auth/session");
  expect(response.status()).toBe(200);
  await expect(response.json()).resolves.toEqual({ user: null });
});

test("mobile navigation closes outside, on Escape and after selection", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "mobile-chromium", "The compact menu only renders below the desktop breakpoint.");
  await page.goto("/");
  const trigger = page.getByRole("button", { name: "Open menu" });
  const menu = page.getByRole("navigation", { name: "Mobile navigation" });

  await trigger.click();
  await expect(menu).toBeVisible();
  const viewport = page.viewportSize();
  await page.mouse.click((viewport?.width ?? 400) - 12, (viewport?.height ?? 800) - 12);
  await expect(menu).toBeHidden();

  await trigger.click();
  await page.keyboard.press("Escape");
  await expect(menu).toBeHidden();
  await expect(trigger).toBeFocused();

  await trigger.click();
  await menu.getByRole("link", { name: "All products" }).click();
  await expect(menu).toBeHidden();
  await expect(page).toHaveURL(/\/products$/);
});

test("fashion category and multiple product URLs survive direct reload with real media", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "The responsive image checks already run in every project.");
  const failedImages: string[] = [];
  page.on("response", (response) => {
    if ((response.url().includes("/media/") || response.url().includes("/_next/image")) && response.status() >= 400) failedImages.push(`${response.status()} ${response.url()}`);
  });
  await page.goto("/categories/hoodies-sweatshirts");
  await expect(page.getByRole("heading", { name: "Hoodies & Sweatshirts" })).toBeVisible();
  await expectLoadedProductImages(page, 5);
  for (const slug of ["clay-zip-hoodie", "black-column-dress", "camel-studio-coat"]) {
    await page.goto(`/products/${slug}`);
    await page.reload();
    await expectLoadedProductImages(page, 1);
    await expect(page.locator('meta[property="og:image"]')).toHaveAttribute("content", /\/media\/demo-fashion\//);
  }
  expect(failedImages).toEqual([]);
});

test("account cart and COD checkout form one real vertical slice", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chromium", "One isolated checkout is enough; responsive rail coverage runs in every project.");
  const suffix = `${Date.now()}-${testInfo.workerIndex}`;
  await page.goto("/register");
  await page.getByLabel("First name").fill("Nour");
  await page.getByLabel("Last name").fill("Test");
  await page.getByLabel("Username").fill(`nour-${suffix}`);
  await page.getByLabel("Email").fill(`nour-${suffix}@example.com`);
  await page.getByLabel("Password").fill("E2e-strong-passphrase-2026!");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/\/account/);

  await page.getByLabel("Recipient").fill("Nour Test");
  await page.getByLabel("Phone").fill("01000000000");
  await page.getByLabel("Address line").fill("12 Test Street");
  await page.getByLabel("City").fill("Cairo");
  await page.getByLabel("Governorate").fill("Cairo");
  await page.getByRole("button", { name: "Save address" }).click();
  await expect(page.getByText("Address saved.")).toBeVisible();

  await page.goto("/products/clay-zip-hoodie");
  await page.getByRole("button", { name: "M", exact: true }).click();
  await page.getByRole("button", { name: /add to bag/i }).click();
  await expect(page.getByText("Added to your bag.")).toBeVisible();
  await page.goto("/cart");
  await expect(page.getByRole("heading", { name: "Clay Zip Hoodie" })).toBeVisible();
  await page.getByRole("link", { name: "Continue to checkout" }).click();
  await page.getByRole("button", { name: "Review authoritative total" }).click();
  await expect(page.getByText("Django-calculated total")).toBeVisible();

  let checkoutRequests = 0;
  let idempotencyKey = "";
  page.on("request", (request) => {
    if (request.url().endsWith("/api/backend/checkout") && request.method() === "POST") {
      checkoutRequests += 1;
      idempotencyKey = request.headers()["idempotency-key"] ?? "";
    }
  });
  await page.getByRole("button", { name: "Place COD order" }).dblclick();
  await expect(page).toHaveURL(/\/orders\/\d+\?placed=1/);
  await expect(page.getByText("Your order is placed.")).toBeVisible();
  expect(checkoutRequests).toBe(1);
  expect(idempotencyKey).not.toBe("");
});
