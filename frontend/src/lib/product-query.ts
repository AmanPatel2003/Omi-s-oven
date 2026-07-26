import type { ProductQueryParams, ProductSort } from "@/types/api";

/** Next.js passes a Server Component's `searchParams` prop as this shape
 * (each value a string, string[], or undefined) — convert it to a real
 * URLSearchParams so server and client code can share one parser. */
export function toURLSearchParams(
  raw: Record<string, string | string[] | undefined>,
): URLSearchParams {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(raw)) {
    if (value == null) continue;
    if (Array.isArray(value)) value.forEach((v) => params.append(key, v));
    else params.set(key, value);
  }
  return params;
}

export function parseProductQueryParams(
  searchParams: URLSearchParams,
): ProductQueryParams {
  const tags = searchParams.getAll("tags");
  return {
    page: searchParams.get("page")
      ? Number(searchParams.get("page"))
      : undefined,
    pageSize: searchParams.get("pageSize")
      ? Number(searchParams.get("pageSize"))
      : undefined,
    search: searchParams.get("search") || undefined,
    category: searchParams.get("category") || undefined,
    minPrice: searchParams.get("minPrice")
      ? Number(searchParams.get("minPrice"))
      : undefined,
    maxPrice: searchParams.get("maxPrice")
      ? Number(searchParams.get("maxPrice"))
      : undefined,
    isEggless: searchParams.get("isEggless") === "true" ? true : undefined,
    tags: tags.length ? tags : undefined,
    sort: (searchParams.get("sort") as ProductSort) || undefined,
  };
}

/** Same query-string-building logic productsApi.ts uses for RTK Query,
 * shared here so the Server Component's plain `fetch` (no RTK Query in the
 * server bundle) produces an identical query string for the identical
 * filters — otherwise the SSR'd list and the client's first refetch could
 * silently disagree. */
export function buildProductQueryString(
  params: ProductQueryParams = {},
): string {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  if (params.search) search.set("search", params.search);
  if (params.category) search.set("category", params.category);
  if (params.minPrice != null) search.set("minPrice", String(params.minPrice));
  if (params.maxPrice != null) search.set("maxPrice", String(params.maxPrice));
  if (params.isEggless != null)
    search.set("isEggless", String(params.isEggless));
  if (params.sort) search.set("sort", params.sort);
  params.tags?.forEach((tag) => search.append("tags", tag));
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}
