"use client";

import {
  useGetFeaturedProductsQuery,
  useGetBestsellersQuery,
  useGetNewArrivalsQuery,
} from "@/store/api/productsApi";
import { ProductRow } from "@/components/products/ProductRow";

export function HomeProductSections() {
  const featured = useGetFeaturedProductsQuery();
  const bestsellers = useGetBestsellersQuery();
  const newArrivals = useGetNewArrivalsQuery();

  return (
    <>
      <ProductRow
        title="Featured"
        products={featured.data}
        isLoading={featured.isLoading}
      />
      <ProductRow
        title="Bestsellers"
        products={bestsellers.data}
        isLoading={bestsellers.isLoading}
      />
      <ProductRow
        title="New Arrivals"
        products={newArrivals.data}
        isLoading={newArrivals.isLoading}
      />
    </>
  );
}
