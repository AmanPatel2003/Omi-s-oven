"use client";

import { useState } from "react";
import { useGetAdminCustomersQuery } from "@/store/api/adminCustomersApi";
import { useDebounce } from "@/hooks/useDebounce";

export function CustomerSearchMultiSelect({
  selectedIds,
  onChange,
}: {
  selectedIds: string[];
  onChange: (ids: string[]) => void;
}) {
  const [searchInput, setSearchInput] = useState("");
  const search = useDebounce(searchInput, 400);
  const { data } = useGetAdminCustomersQuery({ search: search || undefined });

  function toggle(id: string) {
    onChange(
      selectedIds.includes(id)
        ? selectedIds.filter((i) => i !== id)
        : [...selectedIds, id],
    );
  }

  return (
    <div>
      <input
        type="search"
        placeholder="Search customers by name or email…"
        value={searchInput}
        onChange={(e) => setSearchInput(e.target.value)}
        className="w-full rounded-xl border border-crust-200 px-3 py-2 text-sm"
      />

      <div className="mt-2 max-h-48 overflow-y-auto rounded-xl border border-crust-100">
        {data?.items.map((c) => (
          <label
            key={c.id}
            className="flex items-center gap-2 border-b border-crust-50 px-3 py-2 text-sm last:border-0"
          >
            <input
              type="checkbox"
              checked={selectedIds.includes(c.id)}
              onChange={() => toggle(c.id)}
            />
            <span className="text-crust-800">{c.name}</span>
            <span className="text-xs text-crust-400">{c.email}</span>
          </label>
        ))}
        {data && data.items.length === 0 && (
          <p className="p-3 text-sm text-crust-500">No customers match.</p>
        )}
      </div>

      {selectedIds.length > 0 && (
        <p className="mt-2 text-xs text-crust-500">
          {selectedIds.length} selected
        </p>
      )}
    </div>
  );
}
