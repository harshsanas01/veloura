function formatUSD(value: number): string {
  return value.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

export function PriceDisplay({
  basePrice,
  salePrice,
  size = "md",
}: {
  basePrice: number;
  salePrice?: number | null;
  size?: "sm" | "md" | "lg";
}) {
  const textSize = size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-base";
  if (salePrice) {
    return (
      <span className={`flex items-baseline gap-2 ${textSize}`}>
        <span className="font-semibold text-burgundy">{formatUSD(salePrice)}</span>
        <span className="text-ink-secondary line-through">{formatUSD(basePrice)}</span>
      </span>
    );
  }
  return <span className={`font-semibold text-ink ${textSize}`}>{formatUSD(basePrice)}</span>;
}
