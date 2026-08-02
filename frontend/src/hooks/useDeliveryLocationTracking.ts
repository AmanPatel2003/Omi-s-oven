"use client";

import { useEffect, useRef } from "react";
import { usePushLocationMutation } from "@/store/api/staffApi";

const PUSH_INTERVAL_MS = 45_000;

export function useDeliveryLocationTracking(hasActiveDelivery: boolean) {
  const [pushLocation] = usePushLocationMutation();
  const watchIdRef = useRef<number | null>(null);
  const lastPushRef = useRef<number>(0);

  useEffect(() => {
    if (!hasActiveDelivery) {
      if (watchIdRef.current != null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      return;
    }

    if (typeof navigator === "undefined" || !("geolocation" in navigator))
      return;

    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        const now = Date.now();
        if (now - lastPushRef.current < PUSH_INTERVAL_MS) return;
        lastPushRef.current = now;
        pushLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
      },
      () => {},
      { enableHighAccuracy: false, maximumAge: 30_000 },
    );

    return () => {
      if (watchIdRef.current != null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, [hasActiveDelivery, pushLocation]);
}
