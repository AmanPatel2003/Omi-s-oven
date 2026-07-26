"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { useSubmitReviewMutation } from "@/store/api/productsApi";
import { Button } from "@/components/ui/Button";

const reviewSchema = z.object({
  rating: z.coerce.number().min(1, "Pick a rating").max(5),
  comment: z.string().min(5, "Say a little more (min 5 characters)"),
});
type ReviewFormValues = z.infer<typeof reviewSchema>;

export function ReviewForm({ productId }: { productId: string }) {
  const { isAuthenticated } = useAuth();
  const [submitReview, { isLoading }] = useSubmitReviewMutation();
  const [alreadyReviewed, setAlreadyReviewed] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ReviewFormValues>({ resolver: zodResolver(reviewSchema) });

  if (!isAuthenticated) {
    return (
      <p className="text-sm text-crust-600">
        <Link href="/auth/login" className="underline">
          Sign in
        </Link>{" "}
        to leave a review.
      </p>
    );
  }

  async function onSubmit(values: ReviewFormValues) {
    setAlreadyReviewed(false);
    try {
      await submitReview({ productId, ...values }).unwrap();
      setSuccess(true);
      reset();
    } catch (err: unknown) {
      const error = err as { status?: number };
      if (error.status === 409) {
        setAlreadyReviewed(true);
        return;
      }
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-3"
      noValidate
    >
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <label
            key={n}
            className="cursor-pointer text-xl text-crust-300 has-[:checked]:text-crust-600"
          >
            <input
              type="radio"
              value={n}
              className="sr-only"
              {...register("rating")}
            />
            ★
          </label>
        ))}
      </div>
      {errors.rating && (
        <p className="text-sm text-red-600">{errors.rating.message}</p>
      )}

      <textarea
        placeholder="Share your thoughts…"
        rows={3}
        className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        {...register("comment")}
      />
      {errors.comment && (
        <p className="text-sm text-red-600">{errors.comment.message}</p>
      )}

      {alreadyReviewed && (
        <p className="text-sm text-crust-600">
          You've already reviewed this product.
        </p>
      )}
      {success && (
        <p className="text-sm text-green-700">Thanks for your review!</p>
      )}

      <Button type="submit" isLoading={isLoading} className="w-fit">
        Submit review
      </Button>
    </form>
  );
}
