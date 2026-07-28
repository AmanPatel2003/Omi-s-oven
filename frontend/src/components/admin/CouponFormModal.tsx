"use client";

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  useCreateCouponMutation,
  useUpdateCouponMutation,
} from "@/store/api/adminCouponsApi";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import type { AdminCoupon } from "@/types/api";

const couponSchema = z
  .object({
    code: z.string().min(1, "Enter a coupon code"),
    description: z.string().min(1, "Enter a description"),
    discountType: z.enum(["percentage", "flat"]),
    discountValue: z.coerce.number().min(1, "Enter a discount value"),
    maxDiscount: z.coerce.number().optional(),
    usageLimit: z.coerce.number().min(1, "Enter a usage limit"),
    startDate: z.string().min(1, "Pick a start date"),
    endDate: z.string().min(1, "Pick an end date"),
  })
  .refine((v) => new Date(v.endDate) >= new Date(v.startDate), {
    message: "End date must be after the start date",
    path: ["endDate"],
  });
type CouponFormValues = z.infer<typeof couponSchema>;

export function CouponFormModal({
  existing,
  onClose,
}: {
  existing?: AdminCoupon;
  onClose: () => void;
}) {
  const [createCoupon, { isLoading: isCreating }] = useCreateCouponMutation();
  const [updateCoupon, { isLoading: isUpdating }] = useUpdateCouponMutation();
  const isLoading = isCreating || isUpdating;

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<CouponFormValues>({
    resolver: zodResolver(couponSchema),
    defaultValues: existing
      ? {
          code: existing.code,
          description: existing.description,
          discountType: existing.discountType,
          discountValue: existing.discountValue,
          maxDiscount: existing.maxDiscount ?? undefined,
          usageLimit: existing.usageLimit,
          startDate: existing.startDate.slice(0, 10),
          endDate: existing.endDate.slice(0, 10),
        }
      : { discountType: "percentage" },
  });

  const discountType = watch("discountType");

  async function onSubmit(values: CouponFormValues) {
    const payload = {
      ...values,
      maxDiscount:
        values.discountType === "percentage"
          ? (values.maxDiscount ?? null)
          : null,
    };
    if (existing) {
      await updateCoupon({ id: existing.id, ...payload });
    } else {
      await createCoupon(payload);
    }
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-md rounded-xl bg-white p-5">
        <p className="font-medium text-crust-900">
          {existing ? "Edit coupon" : "New coupon"}
        </p>

        <form
          onSubmit={handleSubmit(onSubmit)}
          className="mt-4 flex flex-col gap-3"
          noValidate
        >
          <Field
            label="Code"
            error={errors.code?.message}
            {...register("code")}
          />
          <Field
            label="Description"
            error={errors.description?.message}
            {...register("description")}
          />

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-crust-800">
              Discount type
            </label>
            <Controller
              control={control}
              name="discountType"
              render={({ field }) => (
                <div className="flex gap-4 text-sm text-crust-700">
                  <label className="flex items-center gap-1.5">
                    <input
                      type="radio"
                      checked={field.value === "percentage"}
                      onChange={() => field.onChange("percentage")}
                    />
                    Percentage
                  </label>
                  <label className="flex items-center gap-1.5">
                    <input
                      type="radio"
                      checked={field.value === "flat"}
                      onChange={() => field.onChange("flat")}
                    />
                    Flat
                  </label>
                </div>
              )}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field
              label={
                discountType === "percentage" ? "Discount (%)" : "Discount (₹)"
              }
              type="number"
              error={errors.discountValue?.message}
              {...register("discountValue")}
            />
            {discountType === "percentage" && (
              <Field
                label="Max discount (₹)"
                type="number"
                error={errors.maxDiscount?.message}
                {...register("maxDiscount")}
              />
            )}
          </div>

          <Field
            label="Usage limit"
            type="number"
            error={errors.usageLimit?.message}
            {...register("usageLimit")}
          />

          <div className="grid grid-cols-2 gap-3">
            <Field
              label="Start date"
              type="date"
              error={errors.startDate?.message}
              {...register("startDate")}
            />
            <Field
              label="End date"
              type="date"
              error={errors.endDate?.message}
              {...register("endDate")}
            />
          </div>

          <div className="mt-2 flex justify-end gap-3">
            <Button
              type="button"
              variant="secondary"
              className="w-auto px-4"
              onClick={onClose}
            >
              Cancel
            </Button>
            <Button type="submit" className="w-auto px-4" isLoading={isLoading}>
              {existing ? "Save changes" : "Create coupon"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
