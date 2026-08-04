"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import {
  registerSchema,
  mapPydanticErrors,
  type RegisterFormValues,
} from "@/lib/validators";
import { useRegisterMutation } from "@/store/api/authApi";
import { useAppDispatch } from "@/store/hooks";
import { setCredentials } from "@/store/slices/authSlice";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import type { ValidationErrorResponse } from "@/types/api";

const FIELDS = ["name", "email", "phone", "password"] as const;

export default function RegisterPage() {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [registerUser, { isLoading }] = useRegisterMutation();
  const [emailExists, setEmailExists] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterFormValues) {
    setFormError(null);
    setEmailExists(false);
    try {
      const result = await registerUser(values).unwrap();
      dispatch(
        setCredentials({
          user: result.user,
          access_token: result.access_token,
        }),
      );
      router.push("/account");
    } catch (err: unknown) {
      const error = err as {
        status?: number;
        data?: ValidationErrorResponse | { message?: string };
      };

      // 409 is called out distinctly per the build spec — a clear
      // "this email is taken" message, not lumped in with generic errors.
      if (error.status === 409) {
        setEmailExists(true);
        setError("email", {
          message: "An account with this email already exists.",
        });
        return;
      }

      if (error.status === 422 && error.data && "detail" in error.data) {
        const fieldErrors = mapPydanticErrors(error.data.detail);
        for (const [field, message] of Object.entries(fieldErrors)) {
          if ((FIELDS as readonly string[]).includes(field)) {
            setError(field as (typeof FIELDS)[number], { message });
          }
        }
        return;
      }

      setFormError("Something went wrong. Please try again.");
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center px-4">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Create your account
      </h1>
      <p className="mt-1 text-sm text-crust-600">
        Order custom cakes and track deliveries in one place.
      </p>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mt-6 flex flex-col gap-4"
        noValidate
      >
        <Field
          label="Name"
          autoComplete="name"
          error={errors.name?.message}
          {...register("name")}
        />
        <Field
          label="Email"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register("email")}
        />
        <Field
          label="Phone"
          type="tel"
          autoComplete="tel"
          placeholder="10-digit mobile number"
          error={errors.phone?.message}
          {...register("phone")}
        />
        <Field
          label="Password"
          type="password"
          autoComplete="new-password"
          error={errors.password?.message}
          {...register("password")}
        />

        {emailExists && (
          <p role="alert" className="text-sm text-red-600">
            That email is already registered.{" "}
            <Link href="/auth/login" className="underline">
              Sign in instead
            </Link>
            .
          </p>
        )}
        {formError && (
          <p role="alert" className="text-sm text-red-600">
            {formError}
          </p>
        )}

        <Button type="submit" isLoading={isLoading}>
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-crust-600">
        Already have an account?{" "}
        <Link
          href="/auth/login"
          className="font-medium text-crust-800 underline"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
