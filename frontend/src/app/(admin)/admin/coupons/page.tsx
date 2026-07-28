"use client";

import { useState } from "react";
import Link from "next/link";
import { useGetAdminCouponsQuery } from "@/store/api/adminCouponsApi";
import { DataTable } from "@/components/admin/DataTable";
import { CouponFormModal } from "@/components/admin/CouponFormModal";
import { Button } from "@/components/ui/Button";
import { formatCurrency } from "@/lib/utils";
import type { AdminCoupon } from "@/types/api";

export default function AdminCouponsPage() {
  const { data: coupons, isLoading } = useGetAdminCouponsQuery();
  const [modalCoupon, setModalCoupon] = useState<AdminCoupon | "new" | null>(
    null,
  );

  return (
    <div className="mx-auto max-w-5xl">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          Coupons
        </h1>
        <Button className="w-auto px-4" onClick={() => setModalCoupon("new")}>
          New Coupon
        </Button>
      </div>

      <div className="mt-6">
        <DataTable
          rows={coupons ?? []}
          emptyMessage={isLoading ? "Loading…" : "No coupons yet."}
          columns={[
            {
              header: "Code",
              render: (c) => <span className="font-medium">{c.code}</span>,
            },
            {
              header: "Discount",
              render: (c) =>
                c.discountType === "percentage"
                  ? `${c.discountValue}%${c.maxDiscount ? ` (max ${formatCurrency(c.maxDiscount)})` : ""}`
                  : formatCurrency(c.discountValue),
            },
            {
              header: "Used",
              render: (c) => `${c.usedCount} / ${c.usageLimit}`,
              align: "right",
            },
            {
              header: "Total discount given",
              render: (c) => formatCurrency(c.totalDiscountGiven),
              align: "right",
            },
            {
              header: "",
              render: (c) => (
                <div className="flex justify-end gap-3 text-xs">
                  <button
                    type="button"
                    onClick={() => setModalCoupon(c)}
                    className="text-crust-600 underline"
                  >
                    Edit
                  </button>
                  <Link
                    href={`/admin/coupons/${c.id}/usage`}
                    className="text-crust-600 underline"
                  >
                    Usage
                  </Link>
                </div>
              ),
              align: "right",
            },
          ]}
        />
      </div>

      {modalCoupon && (
        <CouponFormModal
          existing={modalCoupon === "new" ? undefined : modalCoupon}
          onClose={() => setModalCoupon(null)}
        />
      )}
    </div>
  );
}
