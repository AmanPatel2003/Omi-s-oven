"use client";

import { useState } from "react";
import Image from "next/image";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  useGetAdminCustomOrderByIdQuery,
  useSetCustomOrderQuoteMutation,
} from "@/store/api/adminCustomOrdersApi";
import { CustomOrderStatusBadge } from "@/components/custom-orders/CustomOrderStatusBadge";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency, formatDate } from "@/lib/utils";

const quoteSchema = z.object({
  quotedPrice: z.coerce.number().min(1, "Enter a quote amount"),
});
type QuoteFormValues = z.infer<typeof quoteSchema>;

const NEEDS_QUOTE = ["pending", "reviewing"];

export default function AdminCustomOrderDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { data: order, isLoading } = useGetAdminCustomOrderByIdQuery(params.id);
  const [setQuote, { isLoading: isQuoting }] = useSetCustomOrderQuoteMutation();
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<QuoteFormValues>({ resolver: zodResolver(quoteSchema) });

  if (isLoading || !order) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const canQuote = NEEDS_QUOTE.includes(order.status);

  async function onSubmit(values: QuoteFormValues) {
    setSuccess(false);
    await setQuote({ id: order!.id, quotedPrice: values.quotedPrice });
    setSuccess(true);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold text-crust-900">
          {order.occasion}
        </h1>
        <CustomOrderStatusBadge status={order.status} />
      </div>
      <p className="mt-1 text-sm text-crust-500">
        {order.customerName} · {order.customerEmail} · Requested{" "}
        {formatDate(order.createdAt)}
      </p>

      {canQuote ? (
        <div className="mt-6 rounded-xl border-2 border-teal-600 bg-teal-50 p-5">
          <p className="text-sm font-medium text-teal-800">Set a quote</p>
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="mt-3 flex items-end gap-3"
            noValidate
          >
            <div className="flex-1">
              <Field
                label="Quote amount (₹)"
                type="number"
                error={errors.quotedPrice?.message}
                {...register("quotedPrice")}
              />
            </div>
            <Button type="submit" className="w-auto px-4" isLoading={isQuoting}>
              Send Quote
            </Button>
          </form>
          {success && (
            <p className="mt-2 text-sm text-green-700">Quote sent.</p>
          )}
        </div>
      ) : (
        order.quotedPrice != null && (
          <div className="mt-6 rounded-xl border border-crust-100 bg-white p-4">
            <p className="text-sm text-crust-500">Quoted price</p>
            <p className="mt-1 text-2xl font-semibold text-crust-900">
              {formatCurrency(order.quotedPrice)}
            </p>
          </div>
        )
      )}

      <div className="mt-6 flex flex-col gap-4 rounded-xl border border-crust-100 bg-white p-4 text-sm">
        <Detail label="Flavor" value={order.flavor} />
        <Detail label="Size" value={order.size} />
        <Detail label="Shape" value={order.shape} />
        {order.message && (
          <Detail label="Message on cake" value={order.message} />
        )}
        <Detail
          label="Budget"
          value={`${formatCurrency(order.budgetMin)} – ${formatCurrency(order.budgetMax)}`}
        />
        <Detail
          label="Needed by"
          value={formatDate(order.neededBy, "d MMM yyyy, h:mm a")}
        />
        <Detail
          label="Delivery"
          value={order.addressId ? "Delivery" : "Store pickup"}
        />
      </div>

      {order.referenceImages.length > 0 && (
        <section className="mt-6">
          <h2 className="text-sm font-semibold text-crust-800">
            Reference images
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {order.referenceImages.map((url, i) => (
              <div
                key={i}
                className="relative h-24 w-24 overflow-hidden rounded-lg border border-crust-100"
              >
                <Image
                  src={url}
                  alt="Reference"
                  fill
                  className="object-cover"
                />
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-crust-500">{label}</span>
      <span className="text-right text-crust-800">{value}</span>
    </div>
  );
}
