import { notFound } from "next/navigation";
import { ProductGrid } from "@/components/products/ProductGrid";
import type { ApiEnvelope, CategoryWithProducts } from "@/types/api";

async function getCategory(
  slug: string,
  page?: string,
): Promise<CategoryWithProducts | null> {
  const qs = page ? `?page=${page}` : "";
  const res = await fetch(`${process.env.API_URL}/categories/${slug}${qs}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return null;
  const envelope: ApiEnvelope<CategoryWithProducts> = await res.json();
  return envelope.data;
}

export default async function CategoryPage({
  params,
  searchParams,
}: {
  params: { slug: string };
  searchParams: { page?: string };
}) {
  const category = await getCategory(params.slug, searchParams.page);
  if (!category) notFound();

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        {category.name}
      </h1>
      <div className="mt-6">
        <ProductGrid
          products={category.products.items}
          emptyMessage="No products in this category yet."
        />
      </div>
    </div>
  );
}
