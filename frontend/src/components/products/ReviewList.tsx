"use client";

import { useGetReviewsQuery } from "@/store/api/productsApi";
import { formatDate } from "@/lib/utils";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export function ReviewList({ productId }: { productId: string }) {
  const { data: reviews, isLoading } = useGetReviewsQuery(productId);

  console.log("reviews", reviews);
  console.log(Array.isArray(reviews));

  if (isLoading) {
    return (
      <div className="flex justify-center py-6">
        <LoadingSpinner />
      </div>
    );
  }

  if (!reviews || reviews.items.length === 0) {
    return (
      <p className="py-6 text-sm text-crust-500">
        No reviews yet — be the first.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-4">
      {reviews.items?.map((review) => (
        <li key={review.id} className="border-b border-crust-100 pb-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-crust-900">
              {review.userName}
            </span>
            <span className="text-xs text-crust-400">
              {formatDate(review.createdAt)}
            </span>
          </div>
          <div
            className="mt-1 text-sm text-crust-600"
            aria-label={`${review.rating} out of 5 stars`}
          >
            {"★".repeat(review.rating)}
            {"☆".repeat(5 - review.rating)}
          </div>
          <p className="mt-2 text-sm text-crust-700">{review.comment}</p>
        </li>
      ))}
    </ul>
  );
}
