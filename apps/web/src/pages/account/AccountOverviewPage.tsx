import { Link } from "react-router-dom";

import { useCurrentUser } from "@/hooks/useAuth";
import { useOrders } from "@/hooks/useOrders";
import { useWishlist } from "@/hooks/useWishlist";

export function AccountOverviewPage() {
  const user = useCurrentUser();
  const { data: orders } = useOrders();
  const { data: wishlist } = useWishlist();

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-border bg-surface p-6">
          <span className="text-xs uppercase tracking-wider text-ink-secondary">Orders Placed</span>
          <p className="mt-2 font-display text-3xl text-ink">{orders?.length ?? 0}</p>
          <Link to="/account/orders" className="mt-3 inline-block text-sm text-burgundy hover:text-burgundy-hover">
            View order history &rarr;
          </Link>
        </div>
        <div className="rounded-lg border border-border bg-surface p-6">
          <span className="text-xs uppercase tracking-wider text-ink-secondary">Saved Items</span>
          <p className="mt-2 font-display text-3xl text-ink">{wishlist?.items.length ?? 0}</p>
          <Link to="/account/wishlist" className="mt-3 inline-block text-sm text-burgundy hover:text-burgundy-hover">
            View wishlist &rarr;
          </Link>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-6">
        <h2 className="font-display text-xl text-ink">Account Details</h2>
        <dl className="mt-4 space-y-3 text-sm">
          <div className="flex justify-between border-b border-border pb-3">
            <dt className="text-ink-secondary">Full Name</dt>
            <dd className="font-medium text-ink">{user?.full_name}</dd>
          </div>
          <div className="flex justify-between pb-1">
            <dt className="text-ink-secondary">Email</dt>
            <dd className="font-medium text-ink">{user?.email}</dd>
          </div>
        </dl>
      </div>

      <Link
        to="/ai-stylist"
        className="rounded-lg border border-burgundy/20 bg-rose/30 p-6 transition-colors hover:bg-rose/50"
      >
        <span className="text-xs font-semibold uppercase tracking-wider text-burgundy">AI Stylist</span>
        <p className="mt-1 font-display text-xl text-ink">Need styling ideas for your next occasion?</p>
        <p className="mt-1 text-sm text-ink-secondary">Chat with Veloura's AI stylist for a complete look.</p>
      </Link>
    </div>
  );
}
