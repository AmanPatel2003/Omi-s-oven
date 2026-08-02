"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import {
  useGetProfileQuery,
  useUpdateProfileMutation,
  useUpdatePasswordMutation,
} from "@/store/api/usersApi";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  phone: z
    .string()
    .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit mobile number"),
  email: z.string().email("Enter a valid email address"),
});
type ProfileFormValues = z.infer<typeof profileSchema>;

const passwordSchema = z
  .object({
    currentPassword: z.string().min(1, "Enter your current password"),
    newPassword: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string().min(1, "Confirm your new password"),
  })
  .refine((v) => v.newPassword === v.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
type PasswordFormValues = z.infer<typeof passwordSchema>;

export default function AccountPage() {
  const { requireAuth, isHydrating, signOut } = useAuth();
  requireAuth();

  // const { data: profile, isLoading } = useGetProfileQuery();

  const auth = useAuth();

  const { data: profile, isLoading } = useGetProfileQuery(undefined, {
    skip: auth.isHydrating || !auth.isAuthenticated,
  });

  if (isHydrating || isLoading || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-md px-4 py-8">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Account
      </h1>

      <nav className="mt-4 flex gap-4 text-sm text-crust-600 underline">
        <Link href="/account/addresses">Addresses</Link>
        <Link href="/account/rewards">Rewards</Link>
        <Link href="/account/notifications">Notifications</Link>
      </nav>

      <section className="mt-6">
        <h2 className="text-sm font-semibold text-crust-800">Profile</h2>
        <div className="mt-3">
          <ProfileForm
            defaultValues={{
              name: profile.name,
              phone: profile.phone,
              email: profile.email,
            }}
          />
        </div>
      </section>

      <section className="mt-10 border-t border-crust-100 pt-8">
        <h2 className="text-sm font-semibold text-crust-800">
          Change password
        </h2>
        <div className="mt-3">
          <PasswordForm />
        </div>
      </section>

      <Button variant="secondary" className="mt-10 w-fit" onClick={signOut}>
        Sign out
      </Button>
    </div>
  );
}

function ProfileForm({ defaultValues }: { defaultValues: ProfileFormValues }) {
  const [updateProfile, { isLoading }] = useUpdateProfileMutation();
  const [success, setSuccess] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues,
  });

  async function onSubmit(values: ProfileFormValues) {
    setSuccess(false);
    setFormError(null);
    try {
      await updateProfile(values).unwrap();
      setSuccess(true);
    } catch {
      setFormError("Couldn't save your changes. Please try again.");
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-4"
      noValidate
    >
      <Field label="Name" error={errors.name?.message} {...register("name")} />
      <Field
        label="Phone"
        type="tel"
        error={errors.phone?.message}
        {...register("phone")}
      />
      <Field
        label="Email"
        type="email"
        error={errors.email?.message}
        {...register("email")}
      />

      {success && <p className="text-sm text-green-700">Profile updated.</p>}
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <Button type="submit" isLoading={isLoading}>
        Save changes
      </Button>
    </form>
  );
}

function PasswordForm() {
  const [updatePassword, { isLoading }] = useUpdatePasswordMutation();
  const [success, setSuccess] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<PasswordFormValues>({ resolver: zodResolver(passwordSchema) });

  async function onSubmit(values: PasswordFormValues) {
    setSuccess(false);
    setFormError(null);
    try {
      await updatePassword({
        currentPassword: values.currentPassword,
        newPassword: values.newPassword,
      }).unwrap();
      setSuccess(true);
      reset();
    } catch (err: unknown) {
      const error = err as { status?: number };
      if (error.status === 401) {
        setError("currentPassword", {
          message: "Current password is incorrect.",
        });
        return;
      }
      setFormError("Couldn't update your password. Please try again.");
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="flex flex-col gap-4"
      noValidate
    >
      <Field
        label="Current password"
        type="password"
        autoComplete="current-password"
        error={errors.currentPassword?.message}
        {...register("currentPassword")}
      />
      <Field
        label="New password"
        type="password"
        autoComplete="new-password"
        error={errors.newPassword?.message}
        {...register("newPassword")}
      />
      <Field
        label="Confirm new password"
        type="password"
        autoComplete="new-password"
        error={errors.confirmPassword?.message}
        {...register("confirmPassword")}
      />

      {success && <p className="text-sm text-green-700">Password updated.</p>}
      {formError && <p className="text-sm text-red-600">{formError}</p>}

      <Button type="submit" isLoading={isLoading}>
        Update password
      </Button>
    </form>
  );
}
