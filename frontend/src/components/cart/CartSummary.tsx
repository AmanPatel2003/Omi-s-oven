import { useGetCartSummaryQuery } from "@/store/api/cartApi";
import { formatCurrency } from "@/lib/utils";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

export function CartSummary() {
  const { data: summary, isLoading } = useGetCartSummaryQuery();

  if (isLoading || !summary) {
    return (
      <div className="flex justify-center py-6">
        <LoadingSpinner />
      </div>
    );
  }

  const isFreeDelivery = summary.deliveryFee === 0;

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-crust-100 bg-white p-4 text-sm">
      <Row label="Subtotal" value={summary.subtotal} />
      {summary.discount > 0 && (
        <Row
          label="Coupon discount"
          value={-summary.discount}
          highlight="text-green-700"
        />
      )}
      {summary.pointsDiscount > 0 && (
        <Row
          label="Rewards redeemed"
          value={-summary.pointsDiscount}
          highlight="text-green-700"
        />
      )}
      <Row label="Tax" value={summary.tax} />
      <Row
        label="Delivery"
        value={summary.deliveryFee}
        override={isFreeDelivery ? "Free delivery" : undefined}
        highlight={isFreeDelivery ? "text-green-700" : undefined}
      />
      <div className="mt-1 flex justify-between border-t border-crust-100 pt-2 font-semibold text-crust-900">
        <span>Total</span>
        <span>{formatCurrency(summary.total)}</span>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  highlight,
  override,
}: {
  label: string;
  value: number;
  highlight?: string;
  override?: string;
}) {
  return (
    <div className={`flex justify-between text-crust-700 ${highlight ?? ""}`}>
      <span>{label}</span>
      <span>{override ?? formatCurrency(value)}</span>
    </div>
  );
}
