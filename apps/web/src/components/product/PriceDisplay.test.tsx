import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PriceDisplay } from "@/components/product/PriceDisplay";

describe("PriceDisplay", () => {
  it("renders only the base price when there is no sale price", () => {
    render(<PriceDisplay basePrice={49.99} salePrice={null} />);
    expect(screen.getByText("$49.99")).toBeInTheDocument();
  });

  it("renders both the sale price and a struck-through base price when on sale", () => {
    render(<PriceDisplay basePrice={80} salePrice={64} />);
    expect(screen.getByText("$64.00")).toBeInTheDocument();
    expect(screen.getByText("$80.00")).toBeInTheDocument();
  });
});
