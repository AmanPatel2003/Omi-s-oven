"use client";

import { useGetAdminCustomerByIdQuery } from "@/store/api/adminCustomersApi";
import { DataTable } from "@/components/admin/DataTable";
import { RewardAdjustmentForm } from "@/components/admin/RewardAdjustmentForm";
import { OrderStatusBadge } from "@/components/orders/OrderStatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

export default function AdminCustomerDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { data: customer, isLoading } = useGetAdminCustomerByIdQuery(params.id);

  if (isLoading || !customer) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        {customer.name}
      </h1>
      <p className="mt-1 text-sm text-crust-500">
        {customer.email} · {customer.phone}
      </p>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <Stat label="Orders" value={String(customer.orderCount)} />
        <Stat label="Total spend" value={formatCurrency(customer.totalSpend)} />
        <Stat label="Reward points" value={String(customer.rewardPoints)} />
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-[1fr_320px]">
        <div className="flex flex-col gap-6">
          <section>
            <h2 className="text-sm font-semibold text-crust-800">
              Order history
            </h2>
            <div className="mt-3">
              <DataTable
                rows={customer.recentOrders}
                emptyMessage="No orders yet."
                columns={[
                  { header: "Order", render: (o) => `#${o.id.slice(-8)}` },
                  {
                    header: "Status",
                    render: (o) => <OrderStatusBadge status={o.status} />,
                  },
                  { header: "Placed", render: (o) => formatDate(o.createdAt) },
                  {
                    header: "Total",
                    render: (o) => formatCurrency(o.total),
                    align: "right",
                  },
                ]}
              />
            </div>
          </section>

          <section>
            <h2 className="text-sm font-semibold text-crust-800">Addresses</h2>
            {customer.addresses.length === 0 ? (
              <p className="mt-2 text-sm text-crust-500">No saved addresses.</p>
            ) : (
              <div className="mt-3 flex flex-col gap-2">
                {customer.addresses.map((addr) => (
                  <div
                    key={addr.id}
                    className="rounded-xl border border-crust-100 bg-white p-3 text-sm"
                  >
                    <p className="font-medium text-crust-900">
                      {addr.addressType}
                    </p>
                    <p className="text-crust-600">
                      {addr.addressLine1}
                      {addr.addressLine2 ? `, ${addr.addressLine2}` : ""},{" "}
                      {addr.city}, {addr.state} {addr.postalCode}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        <RewardAdjustmentForm customerId={customer.id} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-crust-100 bg-white p-3 text-center">
      <p className="text-lg font-semibold text-crust-900">{value}</p>
      <p className="text-xs text-crust-500">{label}</p>
    </div>
  );
}
