import { zodResolver } from "@hookform/resolvers/zod";
import { Pencil, Star, ThumbsUp, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { useIsAuthenticated } from "@/hooks/useAuth";
import {
  useCreateReview,
  useDeleteReview,
  useReviews,
  useToggleReviewHelpful,
  useUpdateReview,
} from "@/hooks/useReviews";
import type { ReviewSort } from "@/types";
import { cn } from "@/utils/cn";

const reviewSchema = z.object({
  rating: z.number().min(1).max(5),
  title: z.string().min(1, "Title is required.").max(200),
  body: z.string().min(1, "Please write a few words about the product.").max(5000),
});
type ReviewFormValues = z.infer<typeof reviewSchema>;

function Stars({ rating, size = "h-4 w-4" }: { rating: number; size?: string }) {
  return (
    <div className="flex gap-0.5" aria-label={`${rating} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={cn(size, i <= rating ? "fill-burgundy text-burgundy" : "text-taupe/50")}
        />
      ))}
    </div>
  );
}

function StarPicker({ value, onChange }: { value: number; onChange: (v: number) => void }) {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((i) => (
        <button key={i} type="button" onClick={() => onChange(i)} aria-label={`Rate ${i} stars`}>
          <Star className={cn("h-6 w-6", i <= value ? "fill-burgundy text-burgundy" : "text-taupe/50")} />
        </button>
      ))}
    </div>
  );
}

export function ReviewsSection({ productId }: { productId: string }) {
  const isAuthenticated = useIsAuthenticated();
  const [sort, setSort] = useState<ReviewSort>("newest");
  const { data, isLoading } = useReviews(productId, sort);
  const createReview = useCreateReview(productId);
  const updateReview = useUpdateReview(productId);
  const deleteReview = useDeleteReview(productId);
  const toggleHelpful = useToggleReviewHelpful(productId);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ReviewFormValues>({
    resolver: zodResolver(reviewSchema),
    defaultValues: { rating: 5, title: "", body: "" },
  });
  const rating = watch("rating");

  const myReview = data?.items.find((r) => r.is_mine);

  async function onSubmit(values: ReviewFormValues) {
    if (editingId) {
      await updateReview.mutateAsync({ reviewId: editingId, payload: values });
    } else {
      await createReview.mutateAsync(values);
    }
    reset({ rating: 5, title: "", body: "" });
    setShowForm(false);
    setEditingId(null);
  }

  if (isLoading || !data) {
    return <div className="skeleton h-40 w-full rounded" />;
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <Stars rating={Math.round(data.average_rating)} size="h-5 w-5" />
            <span className="font-medium text-ink">{data.average_rating.toFixed(1)}</span>
            <span className="text-sm text-ink-secondary">
              ({data.total} review{data.total === 1 ? "" : "s"})
            </span>
          </div>
        </div>
        {data.total > 0 && (
          <Select
            aria-label="Sort reviews"
            value={sort}
            onChange={(e) => setSort(e.target.value as ReviewSort)}
            className="w-44"
          >
            <option value="newest">Newest</option>
            <option value="highest">Highest Rated</option>
            <option value="lowest">Lowest Rated</option>
            <option value="most_helpful">Most Helpful</option>
          </Select>
        )}
      </div>

      {data.total > 0 && (
        <div className="mt-4 flex flex-col gap-1">
          {([5, 4, 3, 2, 1] as const).map((star) => {
            const key = (["", "one", "two", "three", "four", "five"] as const)[star];
            const count = data.distribution[key as keyof typeof data.distribution];
            const pct = data.total ? Math.round((count / data.total) * 100) : 0;
            return (
              <div key={star} className="flex items-center gap-2 text-xs text-ink-secondary">
                <span className="w-10 shrink-0">{star} star</span>
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-taupe/30">
                  <div className="h-full rounded-full bg-burgundy" style={{ width: `${pct}%` }} />
                </div>
                <span className="w-6 shrink-0 text-right">{count}</span>
              </div>
            );
          })}
        </div>
      )}

      {isAuthenticated && !myReview && !showForm && (
        <Button variant="secondary" size="sm" className="mt-4" onClick={() => setShowForm(true)}>
          Write a Review
        </Button>
      )}
      {!isAuthenticated && (
        <p className="mt-4 text-xs text-ink-secondary">Sign in to write a review.</p>
      )}

      {showForm && (
        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 flex flex-col gap-3 rounded-lg border border-border bg-surface p-4">
          <div>
            <span className="mb-1 block text-sm font-medium text-ink">Your Rating</span>
            <StarPicker value={rating} onChange={(v) => setValue("rating", v)} />
          </div>
          <div>
            <input
              {...register("title")}
              placeholder="Review title"
              className="input-veloura"
            />
            {errors.title && <p className="mt-1 text-xs text-error">{errors.title.message}</p>}
          </div>
          <div>
            <textarea
              {...register("body")}
              rows={4}
              placeholder="What did you think?"
              className="input-veloura resize-none"
            />
            {errors.body && <p className="mt-1 text-xs text-error">{errors.body.message}</p>}
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" isLoading={createReview.isPending || updateReview.isPending}>
              {editingId ? "Update Review" : "Submit Review"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowForm(false);
                setEditingId(null);
                reset({ rating: 5, title: "", body: "" });
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}

      <div className="mt-6 flex flex-col divide-y divide-border">
        {data.items.length === 0 ? (
          <p className="py-4 text-sm text-ink-secondary">This product doesn't have any reviews yet.</p>
        ) : (
          data.items.map((review) => (
            <div key={review.id} className="py-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Stars rating={review.rating} />
                  <span className="text-sm font-medium text-ink">{review.title}</span>
                </div>
                {review.is_mine && (
                  <div className="flex items-center gap-2">
                    <button
                      aria-label="Edit review"
                      onClick={() => {
                        setEditingId(review.id);
                        setShowForm(true);
                        reset({ rating: review.rating, title: review.title, body: review.body });
                      }}
                      className="text-ink-secondary hover:text-ink"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                    <button
                      aria-label="Delete review"
                      onClick={() => deleteReview.mutate(review.id)}
                      className="text-ink-secondary hover:text-error"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </div>
              <div className="mt-1 flex items-center gap-2 text-xs text-ink-secondary">
                <span>{review.author_name}</span>
                {review.is_verified_purchase && (
                  <span className="rounded-full bg-success/10 px-2 py-0.5 font-medium text-success">
                    Verified Purchase
                  </span>
                )}
                <span>{new Date(review.created_at).toLocaleDateString()}</span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{review.body}</p>
              <button
                onClick={() => toggleHelpful.mutate(review.id)}
                className={cn(
                  "mt-2 flex items-center gap-1.5 text-xs font-medium",
                  review.helpful_by_me ? "text-burgundy" : "text-ink-secondary hover:text-ink",
                )}
              >
                <ThumbsUp className="h-3.5 w-3.5" /> Helpful ({review.helpful_count})
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
