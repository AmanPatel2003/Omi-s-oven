"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useGetAddressesQuery } from "@/store/api/addressesApi";
import { useCreateCustomOrderMutation } from "@/store/api/customOrdersApi";
import { ReferenceImagePicker } from "@/components/forms/ReferenceImagePicker";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { MIN_LEAD_TIME_HOURS } from "@/lib/constants";

const customOrderSchema = z
  .object({
    occasion: z.string().min(1, "Tell us the occasion"),
    flavor: z.string().min(1, "Pick a flavor"),
    size: z.string().min(1, "Pick a size"),
    shape: z.string().min(1, "Pick a shape"),
    message: z.string().max(200, "Keep it under 200 characters").optional(),
    budgetMin: z.coerce.number().min(0, "Enter a minimum budget"),
    budgetMax: z.coerce.number().min(0, "Enter a maximum budget"),
    neededBy: z.string().refine(
      (val) => {
        const chosen = new Date(val).getTime();
        const minAllowed = Date.now() + MIN_LEAD_TIME_HOURS * 60 * 60 * 1000;
        return chosen >= minAllowed;
      },
      { message: `Needs to be at least ${MIN_LEAD_TIME_HOURS} hours from now` },
    ),
    deliveryOption: z.enum(["address", "pickup"]),
    addressId: z.string().optional(),
  })
  .refine((v) => v.budgetMax >= v.budgetMin, {
    message: "Max budget must be at least the minimum",
    path: ["budgetMax"],
  })
  .refine((v) => v.deliveryOption === "pickup" || !!v.addressId, {
    message: "Select a delivery address, or choose store pickup",
    path: ["addressId"],
  });

type CustomOrderFormValues = z.infer<typeof customOrderSchema>;

const minNeededByISO = new Date(
  Date.now() + MIN_LEAD_TIME_HOURS * 60 * 60 * 1000,
)
  .toISOString()
  .slice(0, 16);

export function CustomOrderForm() {
  const router = useRouter();
  const { data: addresses } = useGetAddressesQuery();
  const [createCustomOrder, { isLoading }] = useCreateCustomOrderMutation();
  const [, setReferenceFiles] = useState<File[]>([]);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<CustomOrderFormValues>({
    resolver: zodResolver(customOrderSchema),
    defaultValues: { deliveryOption: "pickup" },
  });

  const deliveryOption = watch("deliveryOption");

  async function onSubmit(values: CustomOrderFormValues) {
    setFormError(null);
    try {
      const order = await createCustomOrder({
        occasion: values.occasion,
        flavor: values.flavor,
        size: values.size,
        shape: values.shape,
        message: values.message ?? "",
        budgetMin: values.budgetMin,
        budgetMax: values.budgetMax,
        neededBy: new Date(values.neededBy).toISOString(),
        addressId:
          values.deliveryOption === "pickup"
            ? null
            : (values.addressId ?? null),
        referenceImages: [],
      }).unwrap();
      router.push(`/custom-orders/${order.id}`);
    } catch {
      setFormError("Couldn't submit your request. Please try again.");
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-4"
      noValidate
    >
      <Field
        label="Occasion"
        placeholder="Birthday, anniversary…"
        error={errors.occasion?.message}
        {...register("occasion")}
      />

      <div className="grid grid-cols-2 gap-3">
        <Field
          label="Flavor"
          error={errors.flavor?.message}
          {...register("flavor")}
        />
        <Field
          label="Size"
          placeholder="1kg, 2kg…"
          error={errors.size?.message}
          {...register("size")}
        />
      </div>

      <Field
        label="Shape"
        placeholder="Round, square, heart…"
        error={errors.shape?.message}
        {...register("shape")}
      />

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-crust-800">
          Message on cake (optional)
        </label>
        <textarea
          rows={2}
          maxLength={200}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
          {...register("message")}
        />
        {errors.message && (
          <p className="text-sm text-red-600">{errors.message.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Field
          label="Budget min (₹)"
          type="number"
          error={errors.budgetMin?.message}
          {...register("budgetMin")}
        />
        <Field
          label="Budget max (₹)"
          type="number"
          error={errors.budgetMax?.message}
          {...register("budgetMax")}
        />
      </div>

      <Field
        label="Needed by"
        type="datetime-local"
        min={minNeededByISO}
        error={errors.neededBy?.message}
        {...register("neededBy")}
      />

      <div>
        <p className="text-sm font-medium text-crust-800">Delivery</p>
        <div className="mt-2 flex flex-col gap-2">
          <label className="flex items-center gap-2 text-sm text-crust-700">
            <input
              type="radio"
              value="pickup"
              {...register("deliveryOption")}
            />
            Store pickup
          </label>
          <label className="flex items-center gap-2 text-sm text-crust-700">
            <input
              type="radio"
              value="address"
              {...register("deliveryOption")}
            />
            Deliver to an address
          </label>
        </div>

        {deliveryOption === "address" && (
          <div className="mt-3 flex flex-col gap-2">
            {addresses?.map((addr) => (
              <label
                key={addr.id}
                className="flex items-center gap-2 text-sm text-crust-700"
              >
                <input
                  type="radio"
                  value={addr.id}
                  {...register("addressId")}
                />
                {addr.addressType} — {addr.addressLine1}, {addr.city}
              </label>
            ))}
            {errors.addressId && (
              <p className="text-sm text-red-600">{errors.addressId.message}</p>
            )}
          </div>
        )}
      </div>

      <div>
        <p className="text-sm font-medium text-crust-800">
          Reference images (optional, up to 5)
        </p>
        <div className="mt-2">
          <ReferenceImagePicker onChange={setReferenceFiles} />
        </div>
      </div>

      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <Button type="submit" isLoading={isLoading}>
        Submit request
      </Button>
    </form>
  );
}
