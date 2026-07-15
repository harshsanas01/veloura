import { Star } from "lucide-react";

import { AdminTable } from "@/components/admin/AdminTable";
import { Badge } from "@/components/ui/Badge";
import { useAdminReviews, useModerateReview } from "@/hooks/useAdmin";
import type { Review } from "@/types";

export function AdminReviewsPage() {
  const { data: reviews, isLoading } = useAdminReviews();
  const moderate = useModerateReview();

  return (
    <div>
      <h1 className="font-display text-3xl text-ink">Reviews</h1>
      <p className="mt-1 text-sm text-ink-secondary">Moderate customer product reviews.</p>

      <div className="mt-6">
        {isLoading ? (
          <div className="skeleton h-64 w-full rounded-lg" />
        ) : (
          <AdminTable<Review>
            rows={reviews ?? []}
            emptyMessage="No reviews yet."
            columns={[
              {
                header: "Rating",
                render: (r) => (
                  <span className="flex items-center gap-1">
                    <Star className="h-3.5 w-3.5 fill-burgundy text-burgundy" /> {r.rating}
                  </span>
                ),
              },
              { header: "Title", render: (r) => <span className="font-medium">{r.title}</span> },
              { header: "Author", render: (r) => r.author_name },
              {
                header: "Verified",
                render: (r) => (r.is_verified_purchase ? <Badge variant="success">Verified</Badge> : "—"),
              },
              { header: "Helpful", render: (r) => r.helpful_count },
              { header: "Posted", render: (r) => new Date(r.created_at).toLocaleDateString() },
              {
                header: "Status",
                render: (r) => (
                  <Badge variant={r.is_active ? "success" : "neutral"}>{r.is_active ? "Visible" : "Hidden"}</Badge>
                ),
              },
              {
                header: "Actions",
                render: (r) => (
                  <button
                    className="text-xs font-medium text-burgundy hover:text-burgundy-hover"
                    onClick={() => moderate.mutate({ id: r.id, isActive: !r.is_active })}
                  >
                    {r.is_active ? "Hide" : "Show"}
                  </button>
                ),
              },
            ]}
          />
        )}
      </div>
    </div>
  );
}
