import type { Middleware } from "@reduxjs/toolkit";
import { isRejectedWithValue } from "@reduxjs/toolkit";
import { pushToast } from "@/store/slices/uiSlice";
import { getErrorMessage } from "@/components/shared/ErrorState";

export const toastMiddleware: Middleware = (store) => (next) => (action) => {
  if (
    isRejectedWithValue(action) &&
    typeof action.type === "string" &&
    action.type.includes("/executeMutation/")
  ) {
    const message = getErrorMessage(
      action.payload as Parameters<typeof getErrorMessage>[0],
    );
    store.dispatch(pushToast({ message, variant: "error" }));
  }
  return next(action);
};
