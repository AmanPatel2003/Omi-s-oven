"use client";

import { useGetAdminProductByIdQuery } from "@/store/api/adminProductsApi";
import { AdminProductForm } from "@/components/forms/AdminProductForm";
import { ProductImageUploader } from "@/components/admin/ProductImageUploader";
import { StockAdjustmentPanel } from "@/components/admin/StockAdjustmentPanel";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export default function EditAdminProductPage({
  params,
}: {
  params: { id: string };
}) {
  const { data: product, isLoading } = useGetAdminProductByIdQuery(params.id);

  if (isLoading || !product) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Edit Product
      </h1>

      <section className="mt-6">
        <AdminProductForm existing={product} onSaved={() => {}} />
      </section>

      <section className="mt-10 border-t border-crust-100 pt-8">
        <h2 className="text-sm font-semibold text-crust-800">Images</h2>
        <div className="mt-3">
          <ProductImageUploader
            productId={product.id}
            images={product.images}
          />
        </div>
      </section>

      <section className="mt-10 border-t border-crust-100 pt-8">
        <StockAdjustmentPanel product={product} />
      </section>
    </div>
  );
}
