import { ProductFilters } from "@/components/products/ProductFilters";
import { ProductsBrowser } from "@/components/products/ProductsBrowser";
import { serverFetchProducts } from "@/lib/server-products";

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const initial = await serverFetchProducts(searchParams);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        All Products
      </h1>
      <div className="mt-6 grid gap-6 md:grid-cols-[240px_1fr]">
        <ProductFilters />
        <ProductsBrowser initialProducts={initial.items} />
      </div>
    </div>
  );
}
