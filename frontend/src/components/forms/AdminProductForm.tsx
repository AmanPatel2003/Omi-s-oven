"use client";

import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useGetCategoriesQuery } from "@/store/api/categoriesApi";
import {
  useCreateAdminProductMutation,
  useUpdateAdminProductMutation,
} from "@/store/api/adminProductsApi";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { TagInput } from "@/components/admin/TagInput";
import { VariantRows } from "@/components/admin/VariantRows";
import type { AdminProduct, AdminProductVariant } from "@/types/api";

function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}

const productSchema = z.object({
  name: z.string().min(1, "Enter a product name"),
  slug: z.string().min(1, "Enter a slug"),
  description: z.string().min(1, "Enter a description"),
  category: z.string().min(1, "Select a category"),
  price: z.coerce.number().min(0, "Enter a price"),
  discount_price: z.coerce.number().min(0).optional(),
  is_eggless: z.boolean(),
  low_stock_threshold: z.coerce.number().min(0, "Enter a threshold"),
  stock: z.coerce.number().min(0, "Enter a stock count"),
});

type ProductFormValues = z.infer<typeof productSchema>;
export function AdminProductForm({
  existing,
  onSaved,
}: {
  existing?: AdminProduct;
  onSaved: (product: AdminProduct) => void;
}) {
  const { data: categories } = useGetCategoriesQuery();
  const [createProduct, { isLoading: isCreating }] =
    useCreateAdminProductMutation();
  const [updateProduct, { isLoading: isUpdating }] =
    useUpdateAdminProductMutation();
  const isLoading = isCreating || isUpdating;

  const [tags, setTags] = useState<string[]>(existing?.tags ?? []);
  const [variants, setVariants] = useState<AdminProductVariant[]>(
    existing?.variants ?? [],
  );
  const [slugTouched, setSlugTouched] = useState(!!existing);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    control,
    formState: { errors },
  } = useForm<ProductFormValues>({
    resolver: zodResolver(productSchema),
    defaultValues: existing
      ? {
          name: existing.name,
          slug: existing.slug,
          description: existing.description,
          category: existing.category,
          price: existing.price,
          discount_price: existing.discount_price ?? undefined,
          is_eggless: existing.is_eggless,
          low_stock_threshold: existing.low_stock_threshold,
          stock: existing.stock,
        }
      : {
          is_eggless: false,
          low_stock_threshold: 5,
          stock: 0,
        },
  });

  const name = watch("name");
  if (!slugTouched && name) {
    setValue("slug", slugify(name));
  }

  async function onSubmit(values: ProductFormValues) {
    setFormError(null);
    const payload = {
      ...values,
      discount_price: values.discount_price ?? null,
      tags,
      variants,
    };
    try {
      const product = existing
        ? await updateProduct({ id: existing.id, ...payload }).unwrap()
        : await createProduct(payload).unwrap();
      onSaved(product);
    } catch {
      setFormError("Couldn't save the product. Please try again.");
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-4"
      noValidate
    >
      <Field label="Name" error={errors.name?.message} {...register("name")} />
      <Field
        label="Slug"
        error={errors.slug?.message}
        {...register("slug", { onChange: () => setSlugTouched(true) })}
      />

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-crust-800">
          Description
        </label>
        <textarea
          rows={3}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
          {...register("description")}
        />
        {errors.description && (
          <p className="text-sm text-red-600">{errors.description.message}</p>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-crust-800">Category</label>
        <select
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
          {...register("category")}
        >
          <option value="">Select a category…</option>
          {categories?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {errors.category && (
          <p className="text-sm text-red-600">{errors.category.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Field
          label="Price (₹)"
          type="number"
          error={errors.price?.message}
          {...register("price")}
        />
        <Field
          label="Discount price (₹, optional)"
          type="number"
          error={errors.discount_price?.message}
          {...register("discount_price")}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-crust-800">Tags</label>
        <TagInput value={tags} onChange={setTags} />
      </div>

      <div className="flex flex-col gap-1.5">
        <label className="text-sm font-medium text-crust-800">
          Variants (optional)
        </label>
        <VariantRows variants={variants} onChange={setVariants} />
      </div>

      {variants.length === 0 && (
        <Field
          label="Stock"
          type="number"
          error={errors.stock?.message}
          {...register("stock")}
        />
      )}

      <Field
        label="Low stock threshold"
        type="number"
        error={errors.low_stock_threshold?.message}
        {...register("low_stock_threshold")}
      />

      <Controller
        control={control}
        name="is_eggless"
        render={({ field }) => (
          <label className="flex items-center gap-2 text-sm text-crust-700">
            <input
              type="checkbox"
              checked={field.value}
              onChange={(e) => field.onChange(e.target.checked)}
            />
            Eggless
          </label>
        )}
      />

      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <Button type="submit" isLoading={isLoading}>
        {existing ? "Save changes" : "Create product"}
      </Button>
    </form>
  );
}
