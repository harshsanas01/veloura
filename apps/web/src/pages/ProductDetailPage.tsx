import { Heart, Minus, Plus, Ruler, Share2, Star, X, ZoomIn } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ColorSelector } from "@/components/product/ColorSelector";
import { PriceDisplay } from "@/components/product/PriceDisplay";
import { ProductGrid } from "@/components/product/ProductGrid";
import { ProductRail } from "@/components/product/ProductRail";
import { ReviewsSection } from "@/components/product/ReviewsSection";
import { SizeGuideModal } from "@/components/product/SizeGuideModal";
import { SizeSelector } from "@/components/product/SizeSelector";
import { Accordion } from "@/components/ui/Accordion";
import { Badge } from "@/components/ui/Badge";
import { Breadcrumbs } from "@/components/ui/Breadcrumbs";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { useAddToCart } from "@/hooks/useCart";
import { useIsAuthenticated } from "@/hooks/useAuth";
import { useProduct, useProductsBySlug, useRelatedProducts } from "@/hooks/useProducts";
import { useAlsoBought, useCompleteTheLook } from "@/hooks/useRecommendations";
import { recordRecentlyViewed, useRecentlyViewed } from "@/hooks/useRecentlyViewed";
import { useReviews } from "@/hooks/useReviews";
import { useToggleWishlist } from "@/hooks/useWishlist";
import { useGuestCartStore } from "@/store/guestCartStore";
import { useToastStore } from "@/store/toastStore";
import { useUIStore } from "@/store/uiStore";

export function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: product, isLoading, isError, refetch } = useProduct(slug);
  const { data: related } = useRelatedProducts(product?.id);
  const { data: reviewSummary } = useReviews(product?.id);
  const { data: alsoBought } = useAlsoBought(product?.id);
  const { data: completeTheLook } = useCompleteTheLook(product?.id);
  const addToCart = useAddToCart();
  const { add: addWishlist } = useToggleWishlist();
  const isAuthenticated = useIsAuthenticated();
  const navigate = useNavigate();
  const push = useToastStore((s) => s.push);
  const addGuestItem = useGuestCartStore((s) => s.addItem);
  const openCart = useUIStore((s) => s.openCart);

  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [activeImage, setActiveImage] = useState(0);
  const [zoomOpen, setZoomOpen] = useState(false);
  const [sizeGuideOpen, setSizeGuideOpen] = useState(false);

  const recentSlugs = useRecentlyViewed(slug);
  const { items: recentProducts } = useProductsBySlug(recentSlugs.slice(0, 4));

  useEffect(() => {
    if (slug) recordRecentlyViewed(slug);
  }, [slug]);

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

  const needsColor = (product?.available_colors.length ?? 0) > 0;
  const needsSize = (product?.available_sizes.length ?? 0) > 0;
  const canAddToCart =
    (!needsColor || Boolean(selectedColor)) &&
    (!needsSize || Boolean(selectedVariant)) &&
    (!selectedVariant || selectedVariant.inventory_quantity > 0);
  const isSoldOut = Boolean(selectedVariant) && selectedVariant!.inventory_quantity === 0;
  const isLowStock = Boolean(selectedVariant) && selectedVariant!.inventory_quantity > 0 && selectedVariant!.inventory_quantity <= 3;

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
    if (!canAddToCart || !selectedVariant) {
      if (needsColor && !selectedColor) push("Please select a color.", "error");
      else if (needsSize && !selectedVariant) push("Please select a size.", "error");
      else push("This size and color combination is out of stock.", "error");
      return;
    }
    if (!isAuthenticated) {
      addGuestItem(
        {
          variantId: selectedVariant.id,
          productSlug: product!.slug,
          productName: product!.name,
          productBrand: product!.brand,
          imageUrl: selectedVariant.image_url,
          colorName: selectedVariant.color_name,
          size: selectedVariant.size,
          unitPrice: product!.effective_price,
          inventoryQuantity: selectedVariant.inventory_quantity,
        },
        quantity,
      );
      push("Added to cart.", "success");
      openCart();
      return;
    }
    addToCart.mutate({ variantId: selectedVariant.id, quantity });
  }

  async function handleShare() {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title: product!.name, url });
        return;
      } catch {
        // user cancelled the native share sheet - fall through to clipboard
      }
    }
    await navigator.clipboard.writeText(url);
    push("Link copied to clipboard.", "success");
  }

  const isShoeCategory = product.category.slug === "shoes";

  return (
    <div className="container-veloura py-10">
      <Breadcrumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Shop", to: "/shop" },
          { label: product.category.name, to: `/shop?category=${product.category.slug}` },
          { label: product.name },
        ]}
      />

      <div className="grid gap-10 lg:grid-cols-2">
        <div>
          <button
            type="button"
            onClick={() => setZoomOpen(true)}
            className="group relative block aspect-[3/4] w-full overflow-hidden rounded-lg bg-taupe/10"
            aria-label="View fullscreen image"
          >
            <img
              src={images[activeImage] ?? product.variants[0]?.image_url}
              alt={product.name}
              className="h-full w-full object-cover"
            />
            <span className="absolute bottom-3 right-3 flex h-9 w-9 items-center justify-center rounded-full bg-surface/90 text-ink opacity-0 shadow-card transition-opacity group-hover:opacity-100">
              <ZoomIn className="h-4 w-4" />
            </span>
          </button>
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
            <div className="mt-2 flex items-center gap-1.5 text-xs text-ink-secondary">
              <Star className="h-3.5 w-3.5 fill-burgundy text-burgundy" />
              {reviewSummary && reviewSummary.total > 0 ? (
                <span>
                  {reviewSummary.average_rating.toFixed(1)} ({reviewSummary.total} review
                  {reviewSummary.total === 1 ? "" : "s"})
                </span>
              ) : (
                <span>No reviews yet</span>
              )}
            </div>
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

          {product.available_sizes.length > 0 && (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-medium text-ink">Size</span>
                <button
                  type="button"
                  onClick={() => setSizeGuideOpen(true)}
                  className="flex items-center gap-1 text-xs text-ink-secondary hover:text-ink"
                >
                  <Ruler className="h-3.5 w-3.5" /> Size guide
                </button>
              </div>
              <SizeSelector
                sizes={product.available_sizes}
                selected={selectedSize}
                onSelect={setSelectedSize}
                availableSizes={availableSizes}
              />
              {isSoldOut && <p className="mt-2 text-xs font-medium text-error">Out of stock in this size/color.</p>}
              {isLowStock && (
                <p className="mt-2 text-xs font-medium text-burgundy">
                  Only {selectedVariant!.inventory_quantity} left in stock.
                </p>
              )}
            </div>
          )}

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
              disabled={isSoldOut}
            >
              {isSoldOut ? "Out of Stock" : "Add to Bag"}
            </Button>
            <Button
              variant="secondary"
              size="lg"
              aria-label="Add to wishlist"
              onClick={() => (isAuthenticated ? addWishlist.mutate(product.id) : navigate("/login"))}
            >
              <Heart className="h-4 w-4" />
            </Button>
            <Button variant="secondary" size="lg" aria-label="Share this product" onClick={handleShare}>
              <Share2 className="h-4 w-4" />
            </Button>
          </div>

          <Accordion
            defaultOpen={null}
            sections={[
              {
                title: "Material & Care",
                content: (
                  <>
                    <p><span className="font-medium text-ink">Material:</span> {product.material}</p>
                    <p className="mt-1"><span className="font-medium text-ink">Care:</span> {product.care_instructions}</p>
                  </>
                ),
              },
              {
                title: "Shipping & Returns",
                content: (
                  <>
                    <p>Standard shipping arrives in 4–7 business days; expedited options are available at checkout.</p>
                    <p className="mt-1">Free returns and exchanges within 30 days of delivery, in original condition with tags attached.</p>
                  </>
                ),
              },
            ]}
          />
        </div>
      </div>

      {completeTheLook && completeTheLook.length > 0 && (
        <div className="mt-20">
          <h2 className="mb-6 font-display text-2xl text-ink">Complete the Look</h2>
          <ProductRail products={completeTheLook} />
        </div>
      )}

      <div className="mt-20 max-w-3xl">
        <h2 className="mb-6 font-display text-2xl text-ink">Customer Reviews</h2>
        <ReviewsSection productId={product.id} />
      </div>

      {alsoBought && alsoBought.length > 0 && (
        <div className="mt-20">
          <h2 className="mb-6 font-display text-2xl text-ink">Customers Also Bought</h2>
          <ProductRail products={alsoBought} />
        </div>
      )}

      {related && related.length > 0 && (
        <div className="mt-20">
          <h2 className="mb-6 font-display text-2xl text-ink">You May Also Like</h2>
          <ProductGrid products={related} />
        </div>
      )}

      {recentProducts.length > 0 && (
        <div className="mt-16">
          <h2 className="mb-6 font-display text-2xl text-ink">Recently Viewed</h2>
          <ProductRail products={recentProducts} />
        </div>
      )}

      {zoomOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink/90 p-4"
          onClick={() => setZoomOpen(false)}
        >
          <button
            aria-label="Close fullscreen image"
            className="absolute right-4 top-4 rounded-full bg-surface/20 p-2 text-surface hover:bg-surface/30"
            onClick={() => setZoomOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>
          <img
            src={images[activeImage] ?? product.variants[0]?.image_url}
            alt={product.name}
            className="max-h-full max-w-full rounded object-contain"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      <SizeGuideModal isOpen={sizeGuideOpen} onClose={() => setSizeGuideOpen(false)} isShoe={isShoeCategory} />
    </div>
  );
}
