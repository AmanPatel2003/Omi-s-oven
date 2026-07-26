import {
  buildProductQueryString,
  parseProductQueryParams,
  toURLSearchParams,
} from "@/lib/product-query";
import type { ApiEnvelope, Paginated, Product } from "@/types/api";

const EMPTY: Paginated<Product> = {
  items: [],
  total: 0,
  page: 1,
  pageSize: 24,
};

/** Called only from Server Components — talks to the backend directly with
 * plain `fetch`, no RTK Query, so product listing pages get real SSR'd HTML
 * for SEO before any client JS runs. */
export async function serverFetchProducts(
  rawSearchParams: Record<string, string | string[] | undefined>,
): Promise<Paginated<Product>> {
  const queryParams = parseProductQueryParams(
    toURLSearchParams(rawSearchParams),
  );
  const qs = buildProductQueryString(queryParams);

  const res = await fetch(`${process.env.API_URL}/products${qs}`, {
    next: { revalidate: 60 },
  });
  if (!res.ok) return EMPTY;

  const envelope: ApiEnvelope<Paginated<Product>> = await res.json();
  return envelope.data;
}
