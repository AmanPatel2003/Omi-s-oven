"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import type { Product } from "@/types/api";
import { formatCurrency, cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { useAddToCartMutation } from "@/store/api/cartApi";
import { useAppDispatch } from "@/store/hooks";
import { openCart } from "@/store/slices/uiSlice";

export function ProductCard({ product }: { product: Product }) {
  const hasDiscount = product.discountPrice != null;
  const image = product.images[0];

  const { isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const dispatch = useAppDispatch();
  const [addToCart, { isLoading }] = useAddToCartMutation();

  async function handleAddToCart() {
    if (!isAuthenticated) {
      router.push(`/auth/login?next=${encodeURIComponent(pathname)}`);
      return;
    }
    await addToCart({ productId: product.id, quantity: 1 });
    dispatch(openCart());
  }

  return (
    <div className="flex flex-col overflow-hidden rounded-xl border border-crust-100 bg-white">
      <Link href={`/products/${product.slug}`} className="block">
        <div className="relative aspect-square bg-crust-50">
          {image && (
            <Image
              src={image.url}
              alt={image.alt}
              fill
              sizes="(max-width: 640px) 50vw, 25vw"
              className="object-cover"
            />
          )}
          {!product.inStock && (
            <span className="absolute left-2 top-2 rounded-full bg-crust-900/80 px-2 py-0.5 text-xs text-white">
              Out of stock
            </span>
          )}
        </div>
      </Link>

      <div className="flex flex-1 flex-col gap-1.5 p-3">
        <Link href={`/products/${product.slug}`}>
          <h3 className="line-clamp-2 text-sm font-medium text-crust-900">
            {product.name}
          </h3>
        </Link>

        {product.reviewCount > 0 && (
          <div className="flex items-center gap-1 text-xs text-crust-500">
            <span aria-hidden>★</span>
            <span>{product.avgRating.toFixed(1)}</span>
            <span>({product.reviewCount})</span>
          </div>
        )}

        <div className="mt-auto flex items-baseline gap-2 pt-1">
          <span className="text-sm font-semibold text-crust-900">
            {formatCurrency(
              hasDiscount ? product.discountPrice! : product.price,
            )}
          </span>
          {hasDiscount && (
            <span className="text-xs text-crust-400 line-through">
              {formatCurrency(product.price)}
            </span>
          )}
        </div>

        <Button
          variant="secondary"
          className="mt-2"
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
