"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useDebounce } from "@/hooks/useDebounce";
import { useGetCategoriesQuery } from "@/store/api/categoriesApi";
import { SORT_OPTIONS } from "@/lib/constants";
import type { ProductSort } from "@/types/api";

// The build spec's route list has no dedicated tags endpoint, so this is a
// placeholder set. Swap for a real source (a /tags endpoint, or derived
// from getCategories if the backend nests tags there) once one exists.
const TAG_OPTIONS = [
  "chocolate",
  "vegan",
  "gluten-free",
  "sugar-free",
  "festive",
];

/**
 * Every filter here is read from and written to the URL query string, never
 * to Redux — that's what makes a filtered view shareable/bookmarkable, per
 * the build spec. Changing a filter calls `router.push` with the updated
 * query string; the page/ProductGrid re-renders from `useSearchParams`
 * (or, for the initial SSR page, from the `searchParams` prop Next.js
 * passes to the Server Component).
 */
export function ProductFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { data: categories } = useGetCategoriesQuery();

  const [searchInput, setSearchInput] = useState(
    searchParams.get("search") ?? "",
  );
  const debouncedSearch = useDebounce(searchInput, 400);

  function updateParam(key: string, value: string | null) {
    const params = new URLSearchParams(searchParams.toString());
    if (value === null || value === "") {
      params.delete(key);
    } else {
      params.set(key, value);
    }
    params.delete("page"); // any filter change resets pagination
    router.push(`${pathname}?${params.toString()}`);
  }

  function toggleTag(tag: string) {
    const current = searchParams.getAll("tags");
    const params = new URLSearchParams(searchParams.toString());
    params.delete("tags");
    const next = current.includes(tag)
      ? current.filter((t) => t !== tag)
      : [...current, tag];
    next.forEach((t) => params.append("tags", t));
    params.delete("page");
    router.push(`${pathname}?${params.toString()}`);
  }

  // Push the debounced search term to the URL once it settles.
  useEffect(() => {
    if (debouncedSearch === (searchParams.get("search") ?? "")) return;
    updateParam("search", debouncedSearch || null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch]);

  const activeTags = searchParams.getAll("tags");

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-crust-100 bg-white p-4">
      <input
        type="search"
        placeholder="Search products…"
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
      />

      <div className="grid grid-cols-2 gap-3">
        <select
          value={searchParams.get("category") ?? ""}
          onChange={(e) => updateParam("category", e.target.value || null)}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        >
          <option value="">All categories</option>
          {categories?.map((c) => (
            <option key={c.id} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>

        <select
          value={searchParams.get("sort") ?? "bestselling"}
          onChange={(e) => updateParam("sort", e.target.value as ProductSort)}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Assumes the backend's minPrice/maxPrice query params are in rupees,
          matching what a shopper would type — convert to paise here if your
          backend expects the same paise unit Product.price uses. */}
      <div className="grid grid-cols-2 gap-3">
        <input
          type="number"
          placeholder="Min price (₹)"
          defaultValue={searchParams.get("minPrice") ?? ""}
          onBlur={(e) => updateParam("minPrice", e.target.value || null)}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
        <input
          type="number"
          placeholder="Max price (₹)"
          defaultValue={searchParams.get("maxPrice") ?? ""}
          onBlur={(e) => updateParam("maxPrice", e.target.value || null)}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-crust-700">
        <input
          type="checkbox"
          checked={searchParams.get("isEggless") === "true"}
          onChange={(e) =>
            updateParam("isEggless", e.target.checked ? "true" : null)
          }
        />
        Eggless only
      </label>

      <div className="flex flex-wrap gap-2">
        {TAG_OPTIONS.map((tag) => {
          const active = activeTags.includes(tag);
          return (
            <button
              key={tag}
              type="button"
              onClick={() => toggleTag(tag)}
              className={
                active
                  ? "rounded-full bg-crust-600 px-3 py-1 text-xs text-white"
                  : "rounded-full bg-crust-100 px-3 py-1 text-xs text-crust-700"
              }
            >
              {tag}
            </button>
          );
        })}
      </div>
    </div>
  );
}
