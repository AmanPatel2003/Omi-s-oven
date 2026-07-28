"use client";

import { useState } from "react";
import Link from "next/link";
import {
  useGetAdminProductsQuery,
  useToggleProductAvailabilityMutation,
  useToggleProductFeaturedMutation,
} from "@/store/api/adminProductsApi";
import { useGetCategoriesQuery } from "@/store/api/categoriesApi";
import { DataTable, type DataTableSort } from "@/components/admin/DataTable";
import { Switch } from "@/components/ui/Switch";
import { Button } from "@/components/ui/Button";
import { useDebounce } from "@/hooks/useDebounce";
import { formatCurrency } from "@/lib/utils";

export default function AdminProductsPage() {
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounce(searchInput, 400);
  const [category, setCategory] = useState("");
  const [sort, setSort] = useState<DataTableSort>({
    key: "name",
    direction: "asc",
  });

  const { data: categories } = useGetCategoriesQuery();
  const { data, isLoading } = useGetAdminProductsQuery({
    page,
    search: search || undefined,
    category: category || undefined,
    sort: sort.key,
    sortDir: sort.direction,
  });

  const [toggleAvailability] = useToggleProductAvailabilityMutation();
  const [toggleFeatured] = useToggleProductFeaturedMutation();

  function handleSortChange(key: string) {
    setSort((prev) =>
      prev.key === key
        ? { key, direction: prev.direction === "asc" ? "desc" : "asc" }
        : { key, direction: "asc" },
    );
    setPage(1);
  }

  const totalPages = data
    ? Math.max(1, Math.ceil(data.total / data.pageSize))
    : 1;

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          Products
        </h1>
        <Link href="/admin/products/new">
          <Button className="w-auto px-4">Add Product</Button>
        </Link>
      </div>

      <div className="mt-4 flex flex-wrap gap-3">
        <input
          type="search"
          placeholder="Search products…"
          value={searchInput}
          onChange={(e) => {
            setSearchInput(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
        <select
          value={category}
          onChange={(e) => {
            setCategory(e.target.value);
            setPage(1);
          }}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        >
          <option value="">All categories</option>
          {categories?.map((c) => (
            <option key={c.id} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-4">
        <DataTable
          rows={data?.items ?? []}
          emptyMessage={isLoading ? "Loading…" : "No products found."}
          sort={sort}
          onSortChange={handleSortChange}
          columns={[
            { header: "Name", sortKey: "name", render: (p) => p.name },
            {
              header: "Price",
              sortKey: "price",
              render: (p) => formatCurrency(p.price),
              align: "right",
            },
            {
              header: "Stock",
              render: (p) =>
                p.variants.length > 0
                  ? p.variants.reduce((sum, v) => sum + v.stock, 0)
                  : p.stock,
              align: "right",
            },
            {
              header: "Available",
              render: (p) => (
                <Switch
                  label={`${p.name} available`}
                  checked={p.isAvailable}
                  onChange={() =>
                    toggleAvailability({
                      id: p.id,
                      isAvailable: !p.isAvailable,
                    })
                  }
                />
              ),
            },
            {
              header: "Featured",
              render: (p) => (
                <Switch
                  label={`${p.name} featured`}
                  checked={p.isFeatured}
                  onChange={() =>
                    toggleFeatured({ id: p.id, isFeatured: !p.isFeatured })
                  }
                />
              ),
            },
            {
              header: "",
              render: (p) => (
                <Link
                  href={`/admin/products/${p.id}/edit`}
                  className="text-xs text-crust-600 underline"
                >
                  Edit
                </Link>
              ),
              align: "right",
            },
          ]}
        />
      </div>

      {data && totalPages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-3">
          <Button
            variant="secondary"
            className="w-auto px-3"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="text-sm text-crust-600">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="secondary"
            className="w-auto px-3"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
