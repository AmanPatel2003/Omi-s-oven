import Link from "next/link";
import { HomeProductSections } from "@/components/products/HomeProductSections";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-col items-center gap-4 text-center">
        <h1 className="font-display text-3xl font-semibold text-crust-900">
          The Bakery
        </h1>
        <p className="max-w-xl text-crust-600">
          Fresh bakes, custom cakes, delivered. Cart and checkout land in Module
          3 — for now, browse and sign in.
        </p>
        <Link
          href="/products"
          className="rounded-xl bg-crust-600 px-4 py-2.5 text-sm font-medium text-crust-50"
        >
          Browse products
        </Link>
      </div>

      <HomeProductSections />
    </main>
  );
}
