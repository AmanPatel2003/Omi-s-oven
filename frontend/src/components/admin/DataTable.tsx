"use client";

import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";

export interface DataTableColumn<T> {
  header: string;
  render: (row: T) => React.ReactNode;
  align?: "left" | "right";
}

export function DataTable<T extends { id: string }>({
  columns,
  rows,
  rowHref,
  emptyMessage = "Nothing here.",
}: {
  columns: DataTableColumn<T>[];
  rows: T[];
  rowHref?: (row: T) => string;
  emptyMessage?: string;
}) {
  const router = useRouter();

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-crust-100 bg-white p-6 text-center text-sm text-crust-500">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-crust-100 bg-white">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-crust-100 bg-crust-50">
            {columns.map((col) => (
              <th
                key={col.header}
                className={cn(
                  "px-3 py-2 text-xs font-medium text-crust-500",
                  col.align === "right" ? "text-right" : "text-left",
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              onClick={rowHref ? () => router.push(rowHref(row)) : undefined}
              className={cn(
                "border-b border-crust-50 last:border-0",
                rowHref && "cursor-pointer hover:bg-crust-50",
              )}
            >
              {columns.map((col) => (
                <td
                  key={col.header}
                  className={cn(
                    "px-3 py-2",
                    col.align === "right" ? "text-right" : "text-left",
                  )}
                >
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
