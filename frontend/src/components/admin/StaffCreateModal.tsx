"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useCreateStaffMutation } from "@/store/api/adminStaffApi";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import type { CreateStaffResponse } from "@/types/api";

const staffSchema = z.object({
  name: z.string().min(1, "Enter a name"),
  email: z.string().email("Enter a valid email"),
  phone: z
    .string()
    .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit mobile number"),
  role: z.string().min(1, "Enter a role"),
});
type StaffFormValues = z.infer<typeof staffSchema>;

export function StaffCreateModal({ onClose }: { onClose: () => void }) {
  const [createStaff, { isLoading }] = useCreateStaffMutation();
  const [result, setResult] = useState<CreateStaffResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<StaffFormValues>({ resolver: zodResolver(staffSchema) });

  async function onSubmit(values: StaffFormValues) {
    setFormError(null);
    try {
      const created = await createStaff(values).unwrap();
      setResult(created);
    } catch {
      setFormError("Couldn't create the staff member. Please try again.");
    }
  }

  function copyPassword() {
    if (!result) return;
    navigator.clipboard.writeText(result.tempPassword);
    setCopied(true);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-sm rounded-xl bg-white p-5">
        {!result ? (
          <>
            <p className="font-medium text-crust-900">Add Staff</p>
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="mt-4 flex flex-col gap-3"
              noValidate
            >
              <Field
                label="Name"
                error={errors.name?.message}
                {...register("name")}
              />
              <Field
                label="Email"
                type="email"
                error={errors.email?.message}
                {...register("email")}
              />
              <Field
                label="Phone"
                type="tel"
                error={errors.phone?.message}
                {...register("phone")}
              />
              <Field
                label="Role"
                placeholder="delivery_staff, baker…"
                error={errors.role?.message}
                {...register("role")}
              />

              {formError && <p className="text-sm text-red-600">{formError}</p>}

              <div className="mt-2 flex justify-end gap-3">
                <Button
                  type="button"
                  variant="secondary"
                  className="w-auto px-4"
                  onClick={onClose}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="w-auto px-4"
                  isLoading={isLoading}
                >
                  Create
                </Button>
              </div>
            </form>
          </>
        ) : (
          <>
            <p className="font-medium text-crust-900">
              {result.staff.name} was created
            </p>
            <p className="mt-2 text-sm text-amber-700">
              This temporary password is shown once and won't be retrievable
              again — relay it to {result.staff.name} securely (not over an
              unsecured channel). This app doesn't email it automatically.
            </p>
            <div className="mt-3 flex items-center gap-2 rounded-lg border border-crust-200 bg-crust-50 px-3 py-2">
              <code className="flex-1 text-sm text-crust-900">
                {result.tempPassword}
              </code>
              <button
                type="button"
                onClick={copyPassword}
                className="text-xs text-crust-600 underline"
              >
                {copied ? "Copied" : "Copy"}
              </button>
            </div>
            <Button className="mt-4" onClick={onClose}>
              Done
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
