import { z } from "zod";

// Keep every rule here byte-for-byte in sync with the backend's Pydantic
// validators. If the backend changes a rule, update it here in the same PR —
// client-side validation that drifts from the backend just produces
// confusing "looks valid to me, but the server rejected it" errors.

/** Indian 10-digit mobile number starting 6-9, matches backend `^[6-9]\d{9}$`. */
const phoneRegex = /^[6-9]\d{9}$/;

export const loginSchema = z.object({
  identifier: z
    .string()
    .min(1, "Enter your email or phone number"),
  password: z.string().min(1, "Enter your password"),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Enter a valid email address"),
  phone: z
    .string()
    .regex(phoneRegex, "Enter a valid 10-digit mobile number"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});
export type RegisterFormValues = z.infer<typeof registerSchema>;

export const changePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, "Enter your current password"),
    newPassword: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string().min(1, "Confirm your new password"),
  })
  .refine((vals) => vals.newPassword === vals.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
export type ChangePasswordFormValues = z.infer<typeof changePasswordSchema>;

/**
 * Maps a FastAPI/Pydantic 422 `detail` array onto react-hook-form field
 * errors. Pydantic's `loc` is e.g. ["body", "phone"] — we take the last
 * segment as the field name.
 */
export function mapPydanticErrors(
  detail: Array<{ loc: (string | number)[]; msg: string }>
): Record<string, string> {
  const fieldErrors: Record<string, string> = {};
  for (const err of detail) {
    const field = err.loc[err.loc.length - 1];
    if (typeof field === "string") {
      fieldErrors[field] = err.msg;
    }
  }
  return fieldErrors;
}
