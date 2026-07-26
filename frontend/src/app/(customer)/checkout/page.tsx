"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Script from "next/script";
import { useAuth } from "@/hooks/useAuth";
import { useGetAddressesQuery } from "@/store/api/addressesApi";
import { useGetCartQuery } from "@/store/api/cartApi";
import { useCreateOrderMutation } from "@/store/api/ordersApi";
import {
  useCreatePaymentMutation,
  useVerifyPaymentMutation,
} from "@/store/api/paymentsApi";
import { CartSummary } from "@/components/cart/CartSummary";
import { AddressForm } from "@/components/forms/AddressForm";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn } from "@/lib/utils";
import type { PaymentMethod } from "@/types/api";
import "@/types/razorpay";
import {
  useGetRewardsSummaryQuery,
  useRedeemPointsMutation,
} from "@/store/api/rewardsApi";

type Step = "address" | "review" | "payment";

export default function CheckoutPage() {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const router = useRouter();
  const { data: cart } = useGetCartQuery();
  const { data: addresses, isLoading: isLoadingAddresses } =
    useGetAddressesQuery();

  const [step, setStep] = useState<Step>("address");
  const [selectedAddressId, setSelectedAddressId] = useState<string | null>(
    null,
  );
  const [showAddForm, setShowAddForm] = useState(false);
  const [redeemPoints, setRedeemPoints] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("cod");
  const [razorpayReady, setRazorpayReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: rewardsSummary } = useGetRewardsSummaryQuery();
  const [redeemPointsMutation, { isLoading: isRedeeming }] =
    useRedeemPointsMutation();
  const [pointsRedeemed, setPointsRedeemed] = useState(false); // was: redeemPoints boolean, now driven by an actual server call

  const [createOrder, { isLoading: isCreatingOrder }] =
    useCreateOrderMutation();
  const [createPayment, { isLoading: isCreatingPayment }] =
    useCreatePaymentMutation();
  const [verifyPayment] = useVerifyPaymentMutation();

  const isPlacingOrder = isCreatingOrder || isCreatingPayment;

  async function handlePlaceOrder() {
    if (!selectedAddressId) return;
    setError(null);

    let order;
    try {
      order = await createOrder({
        addressId: selectedAddressId,
        paymentMethod,
        redeemPoints,
      }).unwrap();
    } catch {
      setError("Couldn't place your order. Please try again.");
      return;
    }

    if (paymentMethod === "cod") {
      router.push(`/orders/${order.id}`);
      return;
    }

    if (!window.Razorpay || !razorpayReady) {
      setError(
        "Payment is still loading — please wait a moment and try again.",
      );
      return;
    }

    let payment;
    try {
      payment = await createPayment({ orderId: order.id }).unwrap();
    } catch {
      setError(
        "Couldn't start payment. Your order was created — check Orders to retry payment.",
      );
      return;
    }

    const rzp = new window.Razorpay({
      key: process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID ?? "",
      amount: payment.amount,
      currency: payment.currency,
      order_id: payment.razorpayOrderId,
      name: "The Bakery",
      theme: { color: "#8A5824" },
      handler: async (response) => {
        try {
          await verifyPayment({
            orderId: order.id,
            razorpayPaymentId: response.razorpay_payment_id,
            razorpayOrderId: response.razorpay_order_id,
            razorpaySignature: response.razorpay_signature,
          }).unwrap();
        } finally {
          router.push(`/orders/${order.id}`);
        }
      },
      modal: {
        ondismiss: () => {
          setError(
            "Payment cancelled. Your order was created — you can retry payment from Orders.",
          );
        },
      },
    });
    rzp.open();
  }

  async function togglePointsRedemption() {
    if (!rewardsSummary) return;
    setError(null);
    try {
      if (pointsRedeemed) {
        await redeemPointsMutation({ points: 0 }).unwrap();
        setPointsRedeemed(false);
      } else {
        await redeemPointsMutation({
          points: rewardsSummary.pointsBalance,
        }).unwrap();
        setPointsRedeemed(true);
      }
    } catch {
      setError("Couldn't update points redemption. Please try again.");
    }
  }

  if (isHydrating) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (!cart || cart.items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <p className="text-crust-600">Your cart is empty.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Script
        src="https://checkout.razorpay.com/v1/checkout.js"
        strategy="lazyOnload"
        onLoad={() => setRazorpayReady(true)}
      />
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Checkout
      </h1>
      <div className="mt-6 flex gap-2 text-xs">
        {(["address", "review", "payment"] as Step[]).map((s, i) => (
          <div
            key={s}
            className={cn(
              "flex-1 rounded-full py-1.5 text-center capitalize",
              step === s
                ? "bg-crust-600 text-white"
                : "bg-crust-100 text-crust-500",
            )}
          >
            {i + 1}. {s}
          </div>
        ))}
      </div>
      {step === "address" && (
        <div className="mt-6 flex flex-col gap-4">
          {isLoadingAddresses ? (
            <LoadingSpinner />
          ) : (
            <>
              {addresses?.map((addr) => (
                <label
                  key={addr.id}
                  className={cn(
                    "flex cursor-pointer flex-col gap-1 rounded-xl border p-3 text-sm",
                    selectedAddressId === addr.id
                      ? "border-crust-600 bg-crust-50"
                      : "border-crust-200",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <input
                      type="radio"
                      name="address"
                      checked={selectedAddressId === addr.id}
                      onChange={() => setSelectedAddressId(addr.id)}
                    />
                    <span className="font-medium text-crust-900">
                      {addr.addressType}
                    </span>
                  </div>
                  <p className="pl-6 text-crust-600">
                    {addr.addressLine1}, {addr.city}, {addr.state}{" "}
                    {addr.postalCode}
                  </p>
                </label>
              ))}

              {showAddForm ? (
                <div className="rounded-xl border border-crust-100 p-4">
                  <AddressForm
                    onSaved={(id) => {
                      setSelectedAddressId(id);
                      setShowAddForm(false);
                    }}
                  />
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setShowAddForm(true)}
                  className="text-sm text-crust-600 underline"
                >
                  + Add a new address
                </button>
              )}
            </>
          )}

          <Button
            disabled={!selectedAddressId}
            onClick={() => setStep("review")}
          >
            Continue
          </Button>
        </div>
      )}
      {step === "review" && (
        <div className="mt-6 flex flex-col gap-4">
          <CartSummary />
          <label className="flex items-center gap-2 text-sm text-crust-700">
            <input
              type="checkbox"
              checked={redeemPoints}
              onChange={(e) => setRedeemPoints(e.target.checked)}
            />
            Redeem reward points at checkout
          </label>
          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setStep("address")}>
              Back
            </Button>
            <Button onClick={() => setStep("payment")}>Continue</Button>
          </div>
        </div>
      )}

      {rewardsSummary && rewardsSummary.pointsBalance > 0 && (
        <label className="flex items-center justify-between rounded-xl border border-crust-100 bg-white p-3 text-sm">
          <span className="text-crust-700">
            Use {rewardsSummary.pointsBalance} points
          </span>
          <input
            type="checkbox"
            checked={pointsRedeemed}
            disabled={isRedeeming}
            onChange={togglePointsRedemption}
            className="h-4 w-4"
          />
        </label>
      )}

      {step === "payment" && (
        <div className="mt-6 flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            {(["cod", "online"] as PaymentMethod[]).map((method) => (
              <label
                key={method}
                className={cn(
                  "flex cursor-pointer items-center gap-2 rounded-xl border p-3 text-sm",
                  paymentMethod === method
                    ? "border-crust-600 bg-crust-50"
                    : "border-crust-200",
                )}
              >
                <input
                  type="radio"
                  name="paymentMethod"
                  checked={paymentMethod === method}
                  onChange={() => setPaymentMethod(method)}
                />
                {method === "cod" ? "Cash on Delivery" : "Pay Online"}
              </label>
            ))}
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <div className="flex gap-3">
            <Button variant="secondary" onClick={() => setStep("review")}>
              Back
            </Button>
            <Button onClick={handlePlaceOrder} isLoading={isPlacingOrder}>
              Place Order
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
