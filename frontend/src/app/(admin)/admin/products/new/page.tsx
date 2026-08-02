"use client";

import { useRouter } from "next/navigation";
import { AdminProductForm } from "@/components/forms/AdminProductForm";

export default function NewAdminProductPage() {
  const router = useRouter();

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Add Product
      </h1>
      <p className="mt-1 text-sm text-crust-600">
        Image upload and stock adjustment become available after the product is
        created.
      </p>
      <div className="mt-6">
        <AdminProductForm
          onSaved={(product) =>
            router.push(`/admin/products/${product.id}/edit`)
          }
        />
      </div>
    </div>
  );
}
