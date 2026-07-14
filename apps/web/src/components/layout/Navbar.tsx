import { Heart, Menu, Search, Sparkles, User, X, ShoppingBag } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";

import { useCart } from "@/hooks/useCart";
import { useIsAuthenticated } from "@/hooks/useAuth";
import { useWishlist } from "@/hooks/useWishlist";
import { useUIStore } from "@/store/uiStore";
import { cn } from "@/utils/cn";

const NAV_LINKS = [
  { label: "Women", to: "/shop/women" },
  { label: "Men", to: "/shop/men" },
  { label: "Shop All", to: "/shop" },
  { label: "AI Stylist", to: "/ai-stylist" },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const navigate = useNavigate();
  const isAuthenticated = useIsAuthenticated();
  const toggleCart = useUIStore((s) => s.toggleCart);
  const { data: cart } = useCart();
  const { data: wishlist } = useWishlist();

  function handleSearchSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (searchValue.trim()) {
      navigate(`/shop?q=${encodeURIComponent(searchValue.trim())}`);
      setSearchOpen(false);
      setSearchValue("");
    }
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/95 backdrop-blur">
      <div className="container-veloura flex h-[72px] items-center justify-between gap-4">
        <button
          className="flex items-center justify-center p-1 lg:hidden"
          aria-label="Open menu"
          onClick={() => setMobileOpen(true)}
        >
          <Menu className="h-6 w-6 text-ink" />
        </button>

        <Link to="/" className="font-display text-2xl font-semibold tracking-wide text-ink">
          VELOURA
        </Link>

        <nav className="hidden items-center gap-8 lg:flex">
          {NAV_LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                cn(
                  "text-sm font-medium tracking-wide text-ink-secondary transition-colors hover:text-ink",
                  isActive && "text-ink",
                  link.label === "AI Stylist" && "flex items-center gap-1.5 text-burgundy hover:text-burgundy-hover",
                )
              }
            >
              {link.label === "AI Stylist" && <Sparkles className="h-3.5 w-3.5" />}
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-1 sm:gap-2">
          <button
            aria-label="Search"
            className="rounded-full p-2 text-ink hover:bg-black/5"
            onClick={() => setSearchOpen((v) => !v)}
          >
            <Search className="h-5 w-5" />
          </button>
          <Link
            to={isAuthenticated ? "/account" : "/login"}
            aria-label="Account"
            className="hidden rounded-full p-2 text-ink hover:bg-black/5 sm:block"
          >
            <User className="h-5 w-5" />
          </Link>
          <Link
            to="/account/wishlist"
            aria-label="Wishlist"
            className="relative hidden rounded-full p-2 text-ink hover:bg-black/5 sm:block"
          >
            <Heart className="h-5 w-5" />
            {Boolean(wishlist?.items.length) && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-burgundy text-[10px] text-surface">
                {wishlist!.items.length}
              </span>
            )}
          </Link>
          <button
            aria-label="Cart"
            className="relative rounded-full p-2 text-ink hover:bg-black/5"
            onClick={toggleCart}
          >
            <ShoppingBag className="h-5 w-5" />
            {Boolean(cart?.item_count) && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-burgundy text-[10px] text-surface">
                {cart!.item_count}
              </span>
            )}
          </button>
        </div>
      </div>

      {searchOpen && (
        <div className="border-t border-border bg-surface px-5 py-4">
          <form onSubmit={handleSearchSubmit} className="container-veloura flex items-center gap-3">
            <Search className="h-4 w-4 text-ink-secondary" />
            <input
              autoFocus
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder="Search products, brands, styles..."
              className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-secondary/60"
            />
            <button type="button" onClick={() => setSearchOpen(false)} aria-label="Close search">
              <X className="h-4 w-4 text-ink-secondary" />
            </button>
          </form>
        </div>
      )}

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-ink/40" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 flex h-full w-full max-w-xs flex-col gap-6 bg-surface p-6 shadow-elevated">
            <div className="flex items-center justify-between">
              <span className="font-display text-xl text-ink">Menu</span>
              <button aria-label="Close menu" onClick={() => setMobileOpen(false)}>
                <X className="h-5 w-5 text-ink" />
              </button>
            </div>
            <nav className="flex flex-col gap-5">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileOpen(false)}
                  className="text-lg font-medium text-ink"
                >
                  {link.label}
                </Link>
              ))}
              <hr className="border-border" />
              <Link to={isAuthenticated ? "/account" : "/login"} onClick={() => setMobileOpen(false)} className="text-lg text-ink">
                Account
              </Link>
              <Link to="/account/wishlist" onClick={() => setMobileOpen(false)} className="text-lg text-ink">
                Wishlist
              </Link>
            </nav>
          </div>
        </div>
      )}
    </header>
  );
}
