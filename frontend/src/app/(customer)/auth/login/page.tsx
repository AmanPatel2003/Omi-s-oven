"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { loginSchema, mapPydanticErrors, type LoginFormValues } from "@/lib/validators";
import { useLoginMutation } from "@/store/api/authApi";
import { useAppDispatch } from "@/store/hooks";
import { setCredentials } from "@/store/slices/authSlice";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import type { ValidationErrorResponse } from "@/types/api";

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const dispatch = useAppDispatch();
  const [login, { isLoading }] = useLoginMutation();
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginFormValues) {
    setFormError(null);
    try {
      const result = await login(values).unwrap();
      dispatch(setCredentials({ user: result.user, accessToken: result.accessToken }));
      router.push(searchParams.get("next") ?? "/account");
    } catch (err: unknown) {
      const error = err as { status?: number; data?: ValidationErrorResponse | { message?: string } };

      if (error.status === 422 && error.data && "detail" in error.data) {
        const fieldErrors = mapPydanticErrors(error.data.detail);
        for (const [field, message] of Object.entries(fieldErrors)) {
          if (field === "identifier" || field === "password") {
            setError(field, { message });
          }
        }
        return;
      }

      if (error.status === 401) {
        setFormError("That email/phone or password doesn't match our records.");
        return;
      }

      setFormError("Something went wrong. Please try again.");
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Welcome back
      </h1>
      <p className="mt-1 text-sm text-crust-600">
        Sign in to track orders and reorder your favorites.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-6 flex flex-col gap-4" noValidate>
        <Field
          label="Email or phone"
          type="text"
          autoComplete="username"
          error={errors.identifier?.message}
          {...register("identifier")}
        />
        <Field
          label="Password"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register("password")}
        />

        {formError && (
          <p role="alert" className="text-sm text-red-600">
            {formError}
          </p>
        )}

        <Button type="submit" isLoading={isLoading}>
          Sign in
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-crust-600">
        New here?{" "}
        <Link href="/auth/register" className="font-medium text-crust-800 underline">
          Create an account
        </Link>
      </p>
    </div>
  );
}
