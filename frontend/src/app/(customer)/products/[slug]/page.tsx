import { notFound } from "next/navigation";
import { ProductDetailClient } from "@/components/products/ProductDetailClient";
import { ReviewList } from "@/components/products/ReviewList";
import { ReviewForm } from "@/components/products/ReviewForm";
import type { ApiEnvelope, Product } from "@/types/api";

async function getProduct(slug: string): Promise<Product | null> {
  const res = await fetch(
    `${process.env.NEXT_PUBLIC_API_BASE_URL}/products/${slug}`,
    {
      next: { revalidate: 60 },
    },
  );
  if (!res.ok) return null;
  console.log("This is product page  Response:", res);
  const envelope: ApiEnvelope<Product> = await res.json();
  console.log(envelope.data); // <-- Check this
  return envelope.data;
}

export default async function ProductDetailPage({
  params,
}: {
  params: { slug: string };
}) {
  const product = await getProduct(params.slug);
  if (!product) notFound();

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <ProductDetailClient product={product} />

      <section className="mt-12">
        <h2 className="font-display text-xl font-semibold text-crust-900">
          Reviews
        </h2>
        <div className="mt-4">
          <ReviewForm productId={product.id} />
        </div>
        <div className="mt-6">
          <ReviewList productId={product.id} />
        </div>
      </section>
    </div>
  );
}
