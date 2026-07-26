"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter, usePathname } from "next/navigation";
import type { Product, ProductVariant } from "@/types/api";
import { formatCurrency, cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { useAddToCartMutation } from "@/store/api/cartApi";
import { useAppDispatch } from "@/store/hooks";
import { openCart } from "@/store/slices/uiSlice";

export function ProductDetailClient({ product }: { product: Product }) {
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(
    product.variants[0] ?? null,
  );
  const [activeImage, setActiveImage] = useState(0);

  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useAppDispatch();
  const [addToCart, { isLoading }] = useAddToCartMutation();

  const displayPrice =
    selectedVariant?.price ?? product.discountPrice ?? product.price;

  async function handleAddToCart() {
    if (!isAuthenticated) {
      router.push(`/auth/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    await addToCart({
      productId: product.id,
      variantId: selectedVariant?.id,
      quantity: 1,
    });
    dispatch(openCart());
  }

  return (
    <div className="grid gap-8 sm:grid-cols-2">
      <div>
        <div className="relative aspect-square overflow-hidden rounded-xl bg-crust-50">
          {product.images[activeImage] && (
            <Image
              src={product.images[activeImage].url}
              alt={product.images[activeImage].alt}
              fill
              sizes="(max-width: 640px) 100vw, 50vw"
              className="object-cover"
              priority
            />
          )}
        </div>
        {product.images.length > 1 && (
          <div className="mt-3 flex gap-2">
            {product.images.map((img, i) => (
              <button
                key={img.id}
                type="button"
                onClick={() => setActiveImage(i)}
                className={cn(
                  "relative h-16 w-16 overflow-hidden rounded-lg border",
                  i === activeImage ? "border-crust-600" : "border-crust-100",
                )}
              >
                <Image
                  src={img.url}
                  alt={img.alt}
                  fill
                  className="object-cover"
                />
              </button>
            ))}
          </div>
        )}
      </div>

      <div>
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          {product.name}
        </h1>
        {product.reviewCount > 0 && (
          <p className="mt-1 text-sm text-crust-500">
            ★ {product.avgRating.toFixed(1)} ({product.reviewCount} reviews)
          </p>
        )}

        <p className="mt-4 text-xl font-semibold text-crust-900">
          {formatCurrency(displayPrice)}
        </p>

        {product.variants.length > 0 && (
          <div className="mt-4">
            <p className="text-sm font-medium text-crust-800">Size</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {product.variants.map((v) => (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => setSelectedVariant(v)}
                  className={cn(
                    "rounded-xl border px-3 py-1.5 text-sm",
                    v.id === selectedVariant?.id
                      ? "border-crust-600 bg-crust-50"
                      : "border-crust-200",
                  )}
                >
                  {v.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <p className="mt-6 whitespace-pre-line text-sm text-crust-700">
          {product.description}
        </p>

        <Button
          className="mt-6 w-fit"
          disabled={!product.inStock}
          isLoading={isLoading}
          onClick={handleAddToCart}
        >
          {product.inStock ? "Add to Cart" : "Out of stock"}
        </Button>
      </div>
    </div>
  );
}
