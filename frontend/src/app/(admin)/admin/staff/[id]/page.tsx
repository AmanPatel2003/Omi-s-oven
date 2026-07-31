"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAppSelector } from "@/store/hooks";
import {
  useGetStaffByIdQuery,
  useUpdateStaffMutation,
  useDeactivateStaffMutation,
} from "@/store/api/adminStaffApi";
import { useGetStaffAttendanceSummaryQuery } from "@/store/api/adminAttendanceApi";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { Field } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

const staffEditSchema = z.object({
  name: z.string().min(1, "Enter a name"),
  email: z.string().email("Enter a valid email"),
  phone: z
    .string()
    .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit mobile number"),
  role: z.string().min(1, "Enter a role"),
});
type StaffEditFormValues = z.infer<typeof staffEditSchema>;

export default function AdminStaffDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const currentUserRole = useAppSelector((state) => state.auth.user?.role);
  const isSuperAdmin = currentUserRole === "super_admin";

  const { data: staff, isLoading } = useGetStaffByIdQuery(params.id);
  const { data: summary } = useGetStaffAttendanceSummaryQuery(params.id);
  const [updateStaff, { isLoading: isSaving }] = useUpdateStaffMutation();
  const [deactivateStaff, { isLoading: isDeactivating }] =
    useDeactivateStaffMutation();
  const [showDeactivateConfirm, setShowDeactivateConfirm] = useState(false);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<StaffEditFormValues>({
    resolver: zodResolver(staffEditSchema),
    values: staff
      ? {
          name: staff.name,
          email: staff.email,
          phone: staff.phone,
          role: staff.role,
        }
      : undefined,
  });

  if (isLoading || !staff) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  async function onSubmit(values: StaffEditFormValues) {
    setSuccess(false);
    await updateStaff({ id: staff!.id, ...values });
    setSuccess(true);
  }

  async function handleConfirmDeactivate() {
    await deactivateStaff(staff!.id);
    setShowDeactivateConfirm(false);
  }

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        {staff.name}
      </h1>

      <nav className="mt-3 flex gap-4 text-sm text-crust-600 underline">
        <Link href={`/admin/attendance?staffId=${staff.id}`}>
          Attendance history
        </Link>
        <Link href={`/admin/salary?staffId=${staff.id}`}>Salary history</Link>
      </nav>

      {summary && (
        <div className="mt-4 grid grid-cols-4 gap-3">
          <SummaryStat label="Present" value={summary.daysPresent} />
          <SummaryStat label="Absent" value={summary.daysAbsent} />
          <SummaryStat label="Leave" value={summary.daysLeave} />
          <SummaryStat label="Holiday" value={summary.daysHoliday} />
        </div>
      )}

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mt-6 flex flex-col gap-4"
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
          error={errors.role?.message}
          {...register("role")}
        />

        {success && <p className="text-sm text-green-700">Saved.</p>}

        <Button type="submit" isLoading={isSaving}>
          Save changes
        </Button>
      </form>

      {isSuperAdmin && staff.isActive && (
        <Button
          variant="secondary"
          className="mt-4 w-fit text-red-600"
          onClick={() => setShowDeactivateConfirm(true)}
        >
          Deactivate staff member
        </Button>
      )}

      {showDeactivateConfirm && (
        <ConfirmDialog
          title={`Deactivate ${staff.name}?`}
          description="They'll lose access immediately. This can be reversed by an admin later if needed."
          isDangerous
          isLoading={isDeactivating}
          confirmLabel="Deactivate"
          onConfirm={handleConfirmDeactivate}
          onCancel={() => setShowDeactivateConfirm(false)}
        />
      )}
    </div>
  );
}

function SummaryStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-crust-100 bg-white p-3 text-center">
      <p className="text-xl font-semibold text-crust-900">{value}</p>
      <p className="text-xs text-crust-500">{label}</p>
    </div>
  );
}
