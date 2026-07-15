import { useMemo, useState } from "react";

import { ColorSelector } from "@/components/product/ColorSelector";
import { SizeSelector } from "@/components/product/SizeSelector";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { useMoveWishlistItemToCart } from "@/hooks/useWishlist";
import { useProduct } from "@/hooks/useProducts";

export function MoveToCartModal({
  productId,
  productSlug,
  onClose,
}: {
  productId: string;
  productSlug: string;
  onClose: () => void;
}) {
  const { data: product, isLoading } = useProduct(productSlug);
  const moveToCart = useMoveWishlistItemToCart();
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);

  const variantsForColor = useMemo(
    () => product?.variants.filter((v) => !selectedColor || v.color_name === selectedColor) ?? [],
    [product, selectedColor],
  );
  const availableSizes = useMemo(
    () => new Set(variantsForColor.filter((v) => v.inventory_quantity > 0).map((v) => v.size)),
    [variantsForColor],
  );
  const selectedVariant = variantsForColor.find((v) => v.size === selectedSize);

  return (
    <Modal isOpen onClose={onClose} title="Select Size & Color">
      {isLoading || !product ? (
        <div className="skeleton h-40 w-full rounded" />
      ) : (
        <div className="flex flex-col gap-5">
          {product.available_colors.length > 0 && (
            <div>
              <span className="mb-2 block text-sm font-medium text-ink">Color</span>
              <ColorSelector
                colors={product.available_colors}
                selected={selectedColor}
                onSelect={(c) => {
                  setSelectedColor(c);
                  setSelectedSize(null);
                }}
              />
            </div>
          )}
          <div>
            <span className="mb-2 block text-sm font-medium text-ink">Size</span>
            <SizeSelector
              sizes={product.available_sizes}
              selected={selectedSize}
              onSelect={setSelectedSize}
              availableSizes={availableSizes}
            />
          </div>
          <Button
            className="w-full"
            disabled={!selectedVariant}
            isLoading={moveToCart.isPending}
            onClick={() =>
              selectedVariant &&
              moveToCart.mutate(
                { productId, variantId: selectedVariant.id },
                { onSuccess: onClose },
              )
            }
          >
            Add to Bag
          </Button>
        </div>
      )}
    </Modal>
  );
}
