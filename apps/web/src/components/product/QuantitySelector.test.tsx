import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { QuantitySelector } from "@/components/product/QuantitySelector";

describe("QuantitySelector", () => {
  it("calls onChange with an incremented value when the plus button is clicked", () => {
    const onChange = vi.fn();
    render(<QuantitySelector value={2} onChange={onChange} min={1} max={5} />);

    fireEvent.click(screen.getByLabelText("Increase quantity"));
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it("disables the decrease button at the minimum", () => {
    render(<QuantitySelector value={1} onChange={vi.fn()} min={1} max={5} />);
    expect(screen.getByLabelText("Decrease quantity")).toBeDisabled();
  });

  it("disables the increase button at the maximum", () => {
    render(<QuantitySelector value={5} onChange={vi.fn()} min={1} max={5} />);
    expect(screen.getByLabelText("Increase quantity")).toBeDisabled();
  });
});
