import { describe, expect, it } from "vitest";

import { formatEgp } from "@/shared/lib/money";

describe("formatEgp", () => {
  it("formats Django decimal strings as EGP", () => {
    expect(formatEgp("1890.00")).toContain("1,890");
    expect(formatEgp("1890.00")).toContain("EGP");
  });

  it("does not leak NaN into the interface", () => {
    expect(formatEgp("not-a-price")).not.toContain("NaN");
  });
});
