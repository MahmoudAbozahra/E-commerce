import { describe, expect, it } from "vitest";

import { circularIndex, circularOffset } from "@/shared/lib/circular-carousel";

describe("circular carousel math", () => {
  it("wraps indexes in either direction", () => {
    expect(circularIndex(5, 5)).toBe(0);
    expect(circularIndex(-1, 5)).toBe(4);
  });

  it("chooses the shortest position around the orbit", () => {
    expect(circularOffset(0, 4, 6)).toBe(2);
    expect(circularOffset(5, 0, 6)).toBe(-1);
    expect(circularOffset(2, 2, 6)).toBe(0);
  });
});
