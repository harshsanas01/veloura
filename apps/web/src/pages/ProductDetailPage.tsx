import { Heart, Minus, Plus, Ruler } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ColorSelector } from "@/components/product/ColorSelector";
import { PriceDisplay } from "@/components/product/PriceDisplay";
import { ProductGrid } from "@/components/product/ProductGrid";
import { SizeSelector } from "@/components/product/SizeSelector";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { useAddToCart } from "@/hooks/useCart";
import { useIsAuthenticated } from "@/hooks/useAuth";
import { useProduct, useRelatedProducts } from "@/hooks/useProducts";
import { useToggleWishlist } from "@/hooks/useWishlist";
import { useToastStore } from "@/store/toastStore";

export function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: product, isLoading, isError, refetch } = useProduct(slug);
  const { data: related } = useRelatedProducts(product?.id);
  const addToCart = useAddToCart();
  const { add: addWishlist } = useToggleWishlist();
  const isAuthenticated = useIsAuthenticated();
  const navigate = useNavigate();
  const push = useToastStore((s) => s.push);

  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [activeImage, setActiveImage] = useState(0);

  const variantsForColor = useMemo(
    () => product?.variants.filter((v) => !selectedColor || v.color_name === selectedColor) ?? [],
    [product, selectedColor],
  );
  const availableSizes = useMemo(
    () => new Set(variantsForColor.filter((v) => v.inventory_quantity > 0).map((v) => v.size)),
    [variantsForColor],
  );
  const selectedVariant = useMemo(
    () => variantsForColor.find((v) => v.size === selectedSize),
    [variantsForColor, selectedSize],
  );
  const images = useMemo(() => {
    const urls = Array.from(new Set(variantsForColor.map((v) => v.image_url)));
    return urls.length ? urls : product?.variants.map((v) => v.image_url) ?? [];
  }, [variantsForColor, product]);

  if (isLoading) {
    return (
      <div className="container-veloura grid gap-10 py-10 lg:grid-cols-2">
        <div className="skeleton aspect-[3/4] w-full rounded-lg" />
        <div className="space-y-4">
          <div className="skeleton h-4 w-1/4 rounded" />
          <div className="skeleton h-8 w-2/3 rounded" />
          <div className="skeleton h-4 w-1/3 rounded" />
          <div className="skeleton h-24 w-full rounded" />
        </div>
      </div>
    );
  }

  if (isError || !product) {
    return (
      <div className="container-veloura py-10">
        <ErrorState title="Product not found" description="This item may have been removed." onRetry={() => refetch()} />
      </div>
    );
  }

  function handleAddToCart() {
    if (!isAuthenticated) {
      navigate("/login");
      return;
    }
    if (!selectedVariant) {
      push("Please select a size and color.", "error");
      return;
    }
    addToCart.mutate({ variantId: selectedVariant.id, quantity });
  }

  return (
    <div className="container-veloura py-10">
      <nav className="mb-6 text-xs text-ink-secondary">
        <Link to="/shop" className="hover:text-ink">Shop</Link> /{" "}
        <Link to={`/shop?category=${product.category.slug}`} className="hover:text-ink">
          {product.category.name}
        </Link>
      </nav>

      <div className="grid gap-10 lg:grid-cols-2">
        <div>
          <div className="aspect-[3/4] overflow-hidden rounded-lg bg-taupe/10">
            <img
              src={images[activeImage] ?? product.variants[0]?.image_url}
              alt={product.name}
              className="h-full w-full object-cover"
            />
          </div>
          {images.length > 1 && (
            <div className="mt-3 flex gap-2">
              {images.map((img, i) => (
                <button
                  key={img}
                  onClick={() => setActiveImage(i)}
                  className={`h-16 w-14 overflow-hidden rounded border-2 ${
                    activeImage === i ? "border-burgundy" : "border-transparent"
                  }`}
                >
                  <img src={img} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-5 lg:pl-6">
          <div>
            <span className="text-xs uppercase tracking-wider text-ink-secondary">{product.brand}</span>
            <h1 className="mt-1 font-display text-3xl text-ink">{product.name}</h1>
            <div className="mt-3">
              <PriceDisplay basePrice={product.base_price} salePrice={product.sale_price} size="lg" />
            </div>
          </div>

          <p className="text-sm leading-relaxed text-ink-secondary">{product.description}</p>

          <div className="flex flex-wrap gap-2">
            {product.style_tags.map((tag) => (
              <Badge key={tag} variant="neutral">{tag}</Badge>
            ))}
          </div>

          {product.available_colors.length > 0 && (
            <div>
              <span className="mb-2 block text-sm font-medium text-ink">
                Color {selectedColor && <span className="text-ink-secondary">— {selectedColor}</span>}
              </span>
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
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-ink">Size</span>
              <span className="flex items-center gap-1 text-xs text-ink-secondary">
                <Ruler className="h-3.5 w-3.5" /> Size guide
              </span>
            </div>
            <SizeSelector
              sizes={product.available_sizes}
              selected={selectedSize}
              onSelect={setSelectedSize}
              availableSizes={availableSizes}
            />
          </div>

          <div>
            <span className="mb-2 block text-sm font-medium text-ink">Quantity</span>
            <div className="inline-flex items-center rounded border border-border">
              <button
                aria-label="Decrease quantity"
                className="flex h-10 w-10 items-center justify-center disabled:opacity-30"
                disabled={quantity <= 1}
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
              >
                <Minus className="h-4 w-4" />
              </button>
              <span className="w-8 text-center text-sm tabular-nums">{quantity}</span>
              <button
                aria-label="Increase quantity"
                className="flex h-10 w-10 items-center justify-center disabled:opacity-30"
                disabled={Boolean(selectedVariant) && quantity >= selectedVariant!.inventory_quantity}
                onClick={() => setQuantity((q) => q + 1)}
              >
                <Plus className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              className="flex-1"
              size="lg"
              onClick={handleAddToCart}
              isLoading={addToCart.isPending}
              disabled={product.available_sizes.length > 0 && !selectedVariant}
            >
              {selectedVariant && selectedVariant.inventory_quantity === 0 ? "Out of Stock" : "Add to Bag"}
            </Button>
            <Button
              variant="secondary"
              size="lg"
              aria-label="Add to wishlist"
              onClick={() => (isAuthenticated ? addWishlist.mutate(product.id) : navigate("/login"))}
            >
              <Heart className="h-4 w-4" />
            </Button>
          </div>

          <div className="mt-2 border-t border-border pt-5 text-sm text-ink-secondary">
            <p><span className="font-medium text-ink">Material:</span> {product.material}</p>
            <p className="mt-1"><span className="font-medium text-ink">Care:</span> {product.care_instructions}</p>
          </div>
        </div>
      </div>

      {related && related.length > 0 && (
        <div className="mt-20">
          <h2 className="mb-6 font-display text-2xl text-ink">You May Also Like</h2>
          <ProductGrid products={related} />
        </div>
      )}
    </div>
  );
}
