import { describe, expect, it } from "vitest";

import { absoluteMediaUrl, mediaUrl } from "@/shared/lib/urls";

describe("mediaUrl", () => {
  it("normalizes Django absolute and relative media URLs to the same-origin proxy", () => {
    expect(mediaUrl("http://127.0.0.1:8000/media/demo-fashion/coat.webp")).toBe("/media/demo-fashion/coat.webp");
    expect(mediaUrl("/media/demo-fashion/coat.webp")).toBe("/media/demo-fashion/coat.webp");
  });

  it("keeps verified external object-storage URLs and rejects invalid relative paths", () => {
    expect(mediaUrl("https://cdn.example.com/catalog/coat.webp")).toBe("https://cdn.example.com/catalog/coat.webp");
    expect(mediaUrl("products/coat.webp")).toBeNull();
  });

  it("builds an absolute SEO image URL from the public site origin", () => {
    expect(absoluteMediaUrl("/media/demo-fashion/coat.webp", "https://shop.example.com")).toBe(
      "https://shop.example.com/media/demo-fashion/coat.webp",
    );
  });
});
