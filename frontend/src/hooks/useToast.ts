"use client";

import { useAppDispatch } from "@/store/hooks";
import { pushToast } from "@/store/slices/uiSlice";

export function useToast() {
  const dispatch = useAppDispatch();
  return {
    success: (message: string) =>
      dispatch(pushToast({ message, variant: "success" })),
    info: (message: string) =>
      dispatch(pushToast({ message, variant: "info" })),
  };
}
