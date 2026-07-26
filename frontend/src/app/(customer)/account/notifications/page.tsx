"use client";

import { useAuth } from "@/hooks/useAuth";
import {
  useGetNotificationPreferencesQuery,
  useUpdateNotificationPreferencesMutation,
} from "@/store/api/notificationsApi";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import type { NotificationPreferences } from "@/types/api";

export default function NotificationPreferencesPage() {
  const { requireAuth, isHydrating } = useAuth();
  requireAuth();

  const { data: prefs, isLoading } = useGetNotificationPreferencesQuery();
  const [updatePreferences] = useUpdateNotificationPreferencesMutation();

  if (isHydrating || isLoading || !prefs) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  function toggle(key: keyof NotificationPreferences) {
    updatePreferences({ [key]: !prefs![key] });
  }

  return (
    <div className="mx-auto max-w-md px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Notification Preferences
      </h1>
      <div className="mt-6 flex flex-col gap-3">
        <Toggle
          label="Email"
          checked={prefs.email}
          onChange={() => toggle("email")}
        />
        <Toggle
          label="SMS"
          checked={prefs.sms}
          onChange={() => toggle("sms")}
        />
        <Toggle
          label="WhatsApp"
          checked={prefs.whatsapp}
          onChange={() => toggle("whatsapp")}
        />
      </div>
    </div>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <label className="flex items-center justify-between rounded-xl border border-crust-100 bg-white p-3 text-sm">
      <span className="text-crust-800">{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="h-4 w-4"
      />
    </label>
  );
}
