"use client";

import { useState } from "react";
import {
  useGetNotificationsQuery,
  useMarkNotificationReadMutation,
  useMarkAllNotificationsReadMutation,
} from "@/store/api/notificationsApi";
import { formatDate } from "@/lib/utils";

export function NotificationBell() {
  const [open, setOpen] = useState(false);
  const { data: notifications } = useGetNotificationsQuery(undefined, {
    pollingInterval: 30_000,
  });
  const [markRead] = useMarkNotificationReadMutation();
  const [markAllRead] = useMarkAllNotificationsReadMutation();

  const unreadCount =
    notifications?.items?.filter((n) => !n.isRead).length ?? 0;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        className="relative"
      >
        🔔
        {unreadCount > 0 && (
          <span className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-crust-600 text-[10px] text-white">
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setOpen(false)}
            aria-hidden
          />

          <div className="absolute right-0 z-50 mt-2 w-80 rounded-xl border border-crust-100 bg-white shadow-lg">
            <div className="flex items-center justify-between border-b border-crust-100 p-3">
              <p className="text-sm font-medium text-crust-900">
                Notifications
              </p>
              {unreadCount > 0 && (
                <button
                  type="button"
                  onClick={() => markAllRead()}
                  className="text-xs text-crust-600 underline"
                >
                  Mark all read
                </button>
              )}
            </div>

            <div className="max-h-80 overflow-y-auto">
              {!notifications || notifications.length === 0 ? (
                <p className="p-4 text-sm text-crust-500">
                  No notifications yet.
                </p>
              ) : (
                notifications.items.map((n) => (
                  <button
                    key={n.id}
                    type="button"
                    onClick={() => !n.isRead && markRead(n.id)}
                    className={`block w-full border-b border-crust-50 p-3 text-left text-sm last:border-0 ${
                      n.isRead
                        ? "text-crust-500"
                        : "bg-crust-50 font-medium text-crust-900"
                    }`}
                  >
                    <p>{n.title}</p>
                    <p className="text-xs font-normal text-crust-500">
                      {n.message}
                    </p>
                    <p className="mt-1 text-[10px] font-normal text-crust-400">
                      {formatDate(n.createdAt)}
                    </p>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
