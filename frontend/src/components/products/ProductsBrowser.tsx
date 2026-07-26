"use client";

import { useSearchParams } from "next/navigation";
import { useGetProductsQuery } from "@/store/api/productsApi";
import { parseProductQueryParams } from "@/lib/product-query";
import { ProductGrid } from "@/components/products/ProductGrid";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { Product } from "@/types/api";

export function ProductsBrowser({
  initialProducts,
}: {
  initialProducts: Product[];
}) {
  const searchParams = useSearchParams();
  const queryParams = parseProductQueryParams(
    new URLSearchParams(searchParams.toString()),
  );
  const { data, isLoading } = useGetProductsQuery(queryParams);

  const products = data?.items ?? initialProducts;

  return (
    <div>
      {isLoading && !data && (
        <div className="flex justify-center py-8">
          <LoadingSpinner />
        </div>
      )}
      <ProductGrid products={products} />
    </div>
  );
}
