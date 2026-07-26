"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  useAddAddressMutation,
  useUpdateAddressMutation,
} from "@/store/api/addressesApi";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import type { Address, AddressType } from "@/types/api";

const addressSchema = z.object({
  fullName: z.string().min(1, "Enter a full name"),
  phone: z
    .string()
    .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit mobile number"),
  addressLine1: z.string().min(3, "Enter the address line"),
  addressLine2: z.string().optional(),
  city: z.string().min(1, "Enter a city"),
  state: z.string().min(1, "Enter a state"),
  postalCode: z.string().regex(/^\d{6}$/, "Enter a valid 6-digit postal code"),
  landmark: z.string().optional(),
  addressType: z.enum(["Home", "Work", "Other"]),
});
type AddressFormValues = z.infer<typeof addressSchema>;

export function AddressForm({
  existing,
  onSaved,
}: {
  existing?: Address;
  onSaved: (addressId: string) => void;
}) {
  const [addAddress, { isLoading: isAdding }] = useAddAddressMutation();
  const [updateAddress, { isLoading: isUpdating }] = useUpdateAddressMutation();
  const isLoading = isAdding || isUpdating;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AddressFormValues>({
    resolver: zodResolver(addressSchema),
    defaultValues: existing
      ? {
          fullName: existing.fullName,
          phone: existing.phone,
          addressLine1: existing.addressLine1,
          addressLine2: existing.addressLine2 ?? "",
          city: existing.city,
          state: existing.state,
          postalCode: existing.postalCode,
          landmark: existing.landmark ?? "",
          addressType: existing.addressType,
        }
      : { addressType: "Home" },
  });

  async function onSubmit(values: AddressFormValues) {
    const payload = {
      ...values,
      addressLine2: values.addressLine2 || null,
      landmark: values.landmark || null,
    };
    const address = existing
      ? await updateAddress({ id: existing.id, ...payload }).unwrap()
      : await addAddress(payload).unwrap();
    onSaved(address.id);
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-4"
      noValidate
    >
      <Field
        label="Full name"
        error={errors.fullName?.message}
        {...register("fullName")}
      />
      <Field
        label="Phone"
        type="tel"
        error={errors.phone?.message}
        {...register("phone")}
      />
      <Field
        label="Address line 1"
        error={errors.addressLine1?.message}
        {...register("addressLine1")}
      />
      <Field
        label="Address line 2 (optional)"
        error={errors.addressLine2?.message}
        {...register("addressLine2")}
      />
      <div className="grid grid-cols-2 gap-3">
        <Field
          label="City"
          error={errors.city?.message}
          {...register("city")}
        />
        <Field
          label="State"
          error={errors.state?.message}
          {...register("state")}
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field
          label="Postal code"
          error={errors.postalCode?.message}
          {...register("postalCode")}
        />
        <Field
          label="Landmark (optional)"
          error={errors.landmark?.message}
          {...register("landmark")}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-crust-800">
          Address type
        </label>
        <select
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
          {...register("addressType")}
        >
          {(["Home", "Work", "Other"] as AddressType[]).map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      <Button type="submit" isLoading={isLoading}>
        {existing ? "Save changes" : "Save address"}
      </Button>
    </form>
  );
}
