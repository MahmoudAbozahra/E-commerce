import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PurchasePanel } from "@/features/commerce/purchase-panel";
import type { Product } from "@/shared/api/contracts";
import { server } from "@/tests/test-server";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh: vi.fn() }) }));

const product = {
  id: 1,
  name: "Clay Zip Hoodie",
  slug: "clay-zip-hoodie",
  brand: { id: 1, name: "Atelier Cairo", slug: "atelier-cairo", description: "", logo: "", is_active: true, created_at: "2026-01-01" },
  category: { id: 1, name: "Apparel", slug: "apparel", description: "", parent: null, is_active: true, sort_order: 1, created_at: "2026-01-01", updated_at: "2026-01-01" },
  featured: true,
  min_price: "1890.00",
  available: true,
  rating_average: "0.00",
  review_count: 0,
  primary_image: null,
  variants: [
    { id: 10, sku: "CLAY-S", option_values: { size: "S", color: "clay" }, price: "1890.00", stock: 3, low_stock_threshold: 2, is_active: true, product_id: 1, product_name: "Clay Zip Hoodie", product_slug: "clay-zip-hoodie", product_primary_image: null },
    { id: 11, sku: "CLAY-M", option_values: { size: "M", color: "clay" }, price: "1890.00", stock: 2, low_stock_threshold: 2, is_active: true, product_id: 1, product_name: "Clay Zip Hoodie", product_slug: "clay-zip-hoodie", product_primary_image: null },
    { id: 12, sku: "INK-S", option_values: { size: "S", color: "ink" }, price: "1990.00", stock: 4, low_stock_threshold: 2, is_active: true, product_id: 1, product_name: "Clay Zip Hoodie", product_slug: "clay-zip-hoodie", product_primary_image: null },
  ],
} as unknown as Product;

describe("PurchasePanel", () => {
  beforeEach(() => push.mockClear());

  it("selects a real variant and adds it to the authenticated cart", async () => {
    let sent: unknown;
    server.use(http.post("/api/backend/cart/items", async ({ request }) => { sent = await request.json(); return HttpResponse.json({ id: 1 }, { status: 201 }); }));
    render(<PurchasePanel product={product}/>);
    fireEvent.click(screen.getByRole("button", { name: "M" }));
    fireEvent.click(screen.getByRole("button", { name: /add to bag/i }));
    await screen.findByText("Added to your bag.");
    expect(sent).toEqual({ variant_id: 11, quantity: 1 });
  });

  it("sends unauthenticated shoppers to login with a return URL", async () => {
    server.use(http.post("/api/backend/cart/items", () => HttpResponse.json({ error: { detail: "Authentication required" } }, { status: 401 })));
    render(<PurchasePanel product={product}/>);
    fireEvent.click(screen.getByRole("button", { name: /add to bag/i }));
    await waitFor(() => expect(push).toHaveBeenCalledWith("/login?next=%2Fproducts%2Fclay-zip-hoodie"));
  });

  it("rotates visual options and selects the matching real variant", async () => {
    let sent: unknown;
    server.use(http.post("/api/backend/cart/items", async ({ request }) => { sent = await request.json(); return HttpResponse.json({ id: 1 }, { status: 201 }); }));
    const view = render(<PurchasePanel product={product}/>);
    fireEvent.click(view.getByRole("button", { name: "Select color ink" }));
    fireEvent.click(view.getByRole("button", { name: /add to bag/i }));
    await view.findByText("Added to your bag.");
    expect(sent).toEqual({ variant_id: 12, quantity: 1 });
  });
});
