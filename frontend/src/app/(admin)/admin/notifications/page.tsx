"use client";

import { useState } from "react";
import {
  useSendNotificationMutation,
  useBroadcastNotificationMutation,
} from "@/store/api/adminCampaignsApi";
import { CustomerSearchMultiSelect } from "@/components/admin/CustomerSearchMultiSelect";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import type {
  CampaignResult,
  CampaignSegment,
  NotificationChannel,
} from "@/types/api";

type TargetMode = "specific" | "segment" | "broadcast";
const CHANNELS: NotificationChannel[] = ["email", "sms", "whatsapp"];

export default function AdminCampaignsPage() {
  const [channel, setChannel] = useState<NotificationChannel>("email");
  const [targetMode, setTargetMode] = useState<TargetMode>("specific");
  const [customerIds, setCustomerIds] = useState<string[]>([]);
  const [segment, setSegment] = useState<CampaignSegment>({});
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<CampaignResult | null>(null);

  const [sendNotification, { isLoading: isSending }] =
    useSendNotificationMutation();
  const [broadcastNotification, { isLoading: isBroadcasting }] =
    useBroadcastNotificationMutation();
  const isLoading = isSending || isBroadcasting;

  const canSend =
    message.trim().length > 0 &&
    (targetMode !== "specific" || customerIds.length > 0) &&
    (channel !== "email" || subject.trim().length > 0);

  async function handleSend() {
    setResult(null);
    if (targetMode === "broadcast") {
      const res = await broadcastNotification({
        channel,
        subject: channel === "email" ? subject : undefined,
        message,
      }).unwrap();
      setResult(res);
      return;
    }
    const res = await sendNotification({
      channel,
      targetMode,
      customerIds: targetMode === "specific" ? customerIds : undefined,
      segment: targetMode === "segment" ? segment : undefined,
      subject: channel === "email" ? subject : undefined,
      message,
    }).unwrap();
    setResult(res);
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Campaigns
      </h1>

      <div className="mt-4 rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
        Email/SMS/WhatsApp sending is not yet configured — campaigns will be
        logged but not delivered.
      </div>

      <div className="mt-6 flex flex-col gap-5">
        <div>
          <p className="text-sm font-medium text-crust-800">Channel</p>
          <div className="mt-2 flex gap-2">
            {CHANNELS.map((c) => (
              <ChoiceChip
                key={c}
                label={c}
                active={channel === c}
                onClick={() => setChannel(c)}
              />
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-crust-800">Target</p>
          <div className="mt-2 flex gap-2">
            <ChoiceChip
              label="Specific customers"
              active={targetMode === "specific"}
              onClick={() => setTargetMode("specific")}
            />
            <ChoiceChip
              label="Segment"
              active={targetMode === "segment"}
              onClick={() => setTargetMode("segment")}
            />
            <ChoiceChip
              label="Broadcast all"
              active={targetMode === "broadcast"}
              onClick={() => setTargetMode("broadcast")}
            />
          </div>
        </div>

        {targetMode === "specific" && (
          <CustomerSearchMultiSelect
            selectedIds={customerIds}
            onChange={setCustomerIds}
          />
        )}

        {targetMode === "segment" && (
          <div className="grid grid-cols-3 gap-3">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-crust-700">
                Loyalty tier
              </label>
              <input
                value={segment.loyaltyTier ?? ""}
                onChange={(e) =>
                  setSegment((s) => ({
                    ...s,
                    loyaltyTier: e.target.value || undefined,
                  }))
                }
                placeholder="Gold, Silver…"
                className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-crust-700">
                Inactive for (days)
              </label>
              <input
                type="number"
                value={segment.inactiveDays ?? ""}
                onChange={(e) =>
                  setSegment((s) => ({
                    ...s,
                    inactiveDays: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  }))
                }
                className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-crust-700">
                Min orders
              </label>
              <input
                type="number"
                value={segment.minOrders ?? ""}
                onChange={(e) =>
                  setSegment((s) => ({
                    ...s,
                    minOrders: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  }))
                }
                className="rounded-lg border border-crust-200 px-2 py-1.5 text-sm"
              />
            </div>
          </div>
        )}

        {channel === "email" && (
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-crust-800">
              Subject
            </label>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
            />
          </div>
        )}

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-crust-800">Message</label>
          <textarea
            rows={5}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
          />
        </div>

        <Button
          className="w-fit px-6"
          isLoading={isLoading}
          disabled={!canSend}
          onClick={handleSend}
        >
          Send Campaign
        </Button>

        {result && (
          <div className="rounded-xl border border-crust-100 bg-white p-4 text-sm">
            <p className="font-medium text-crust-900">Campaign result</p>
            <div className="mt-2 grid grid-cols-3 gap-3 text-center">
              <ResultStat
                label="Sent"
                value={result.sentCount}
                tone="text-green-700"
              />
              <ResultStat
                label="Failed"
                value={result.failedCount}
                tone="text-red-700"
              />
              <ResultStat
                label="Skipped"
                value={result.skippedCount}
                tone="text-crust-500"
              />
            </div>
            {result.warning && (
              <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
                {result.warning}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ChoiceChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full px-3 py-1.5 text-sm font-medium capitalize",
        active ? "bg-crust-600 text-white" : "bg-crust-100 text-crust-600",
      )}
    >
      {label}
    </button>
  );
}

function ResultStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: string;
}) {
  return (
    <div>
      <p className={cn("text-lg font-semibold", tone)}>{value}</p>
      <p className="text-xs text-crust-500">{label}</p>
    </div>
  );
}
