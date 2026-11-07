import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ProductRail } from "@/features/showcase/product-rail";
import type { Product } from "@/shared/api/contracts";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn(), refresh: vi.fn() }) }));

const product = { id: 1, name: "Clay Zip Hoodie", slug: "clay-zip-hoodie", brand: { name: "Atelier Cairo" }, category: { name: "Apparel", slug: "apparel" }, min_price: "1890.00", available: true, featured: true, rating_average: "0.00", review_count: 0, primary_image: null, variants: [{ id: 1, sku: "CLAY-M", option_values: { size: "M" }, price: "1890.00", stock: 2, is_active: true }] } as unknown as Product;

describe("ProductRail", () => {
  it("opens from keyboard-focusable product buttons and closes with Escape", async () => {
    render(<ProductRail products={[product]}/>);
    const trigger = screen.getByRole("button", { name: /preview clay zip hoodie/i });
    fireEvent.click(trigger);
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(dialog).toHaveStyle({ opacity: "0" }));
  });
});
