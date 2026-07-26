import { ProductCard } from "@/components/products/ProductCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { Product } from "@/types/api";

export function ProductRow({
  title,
  products,
  isLoading,
}: {
  title: string;
  products: Product[] | undefined;
  isLoading: boolean;
}) {
  return (
    <section className="mt-10">
      <h2 className="font-display text-xl font-semibold text-crust-900">
        {title}
      </h2>

      {isLoading ? (
        <div className="mt-4 flex justify-center py-8">
          <LoadingSpinner />
        </div>
      ) : !products || products.length === 0 ? (
        <p className="mt-4 text-sm text-crust-500">Nothing here yet.</p>
      ) : (
        <div className="mt-4 flex gap-4 overflow-x-auto pb-2">
          {products.map((product) => (
            <div key={product.id} className="w-40 flex-shrink-0 sm:w-48">
              <ProductCard product={product} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
