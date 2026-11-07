import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ResilientImage } from "@/shared/ui/resilient-image";

describe("ResilientImage", () => {
  it("shows a labelled fallback after a genuine browser image error", () => {
    render(<div className="relative"><ResilientImage src="/media/missing.webp" alt="Demo coat" fallbackLabel="Image unavailable for Demo coat" fill /></div>);
    fireEvent.error(screen.getByAltText("Demo coat"));
    expect(screen.getByRole("img", { name: "Image unavailable for Demo coat" })).toHaveAttribute("data-image-fallback");
  });
});
