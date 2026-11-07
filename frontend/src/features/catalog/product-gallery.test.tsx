import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProductGallery } from "@/features/catalog/product-gallery";
import type { ProductDetail } from "@/shared/api/contracts";

const product = {
  id: 1,
  name: "Ivory Blazer Set",
  slug: "ivory-blazer-set",
  images: [
    { id: 1, image: "https://example.com/front.webp", alt_text: "Front", sort_order: 0, is_primary: true, product: 1 },
    { id: 2, image: "https://example.com/back.webp", alt_text: "Back", sort_order: 1, is_primary: false, product: 1 },
  ],
} as unknown as ProductDetail;

describe("ProductGallery", () => {
  it("completes a two-image orbit on both sides and rotates with the controls", () => {
    render(<ProductGallery product={product}/>);
    expect(screen.getAllByRole("button", { name: "Rotate to image 2" })).toHaveLength(2);
    fireEvent.click(screen.getByRole("button", { name: "Next product image" }));
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Rotate to image 1" })).toHaveLength(2);
  });
});
