"use client";

import { useState } from "react";
import { useAppSelector } from "@/store/hooks";
import {
  useGetSalaryPreviewQuery,
  useProcessSalaryMutation,
} from "@/store/api/adminSalaryApi";
import { useDownloadSalarySlip } from "@/hooks/useDownloadSalarySlip";
import { ConfirmDialog } from "@/components/admin/ConfirmDialog";
import { DataTable } from "@/components/admin/DataTable";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { formatCurrency } from "@/lib/utils";

export default function AdminSalaryPage() {
  const currentUserRole = useAppSelector((state) => state.auth.user?.role);
  const isSuperAdmin = currentUserRole === "super_admin";

  const [month, setMonth] = useState(new Date().toISOString().slice(0, 7));
  const {
    data: preview,
    isLoading,
    isFetching,
  } = useGetSalaryPreviewQuery(month);
  const [processSalary, { isLoading: isProcessing }] =
    useProcessSalaryMutation();
  const { downloadSlip, isDownloading } = useDownloadSalarySlip();

  const [showConfirm, setShowConfirm] = useState(false);
  const [processedMonth, setProcessedMonth] = useState<string | null>(null);

  async function handleConfirmProcess() {
    const result = await processSalary(month).unwrap();
    if (result.processed) setProcessedMonth(result.month);
    setShowConfirm(false);
  }

  const totalNet = preview?.reduce((sum, row) => sum + row.netSalary, 0) ?? 0;

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="font-display text-2xl font-semibold text-crust-900">
        Salary
      </h1>

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <input
          type="month"
          value={month}
          onChange={(e) => {
            setMonth(e.target.value);
            setProcessedMonth(null);
          }}
          className="rounded-xl border border-crust-200 px-3 py-2 text-sm"
        />
        {isFetching && <LoadingSpinner className="h-4 w-4" />}
      </div>

      {processedMonth === month && (
        <p className="mt-3 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-700">
          Salary for {month} has been processed and finalized.
        </p>
      )}

      <div className="mt-4">
        <DataTable
          rows={(preview ?? []).map((r) => ({ id: r.staffId, ...r }))}
          emptyMessage={
            isLoading ? "Loading…" : "No preview available for this month."
          }
          columns={[
            { header: "Staff", render: (r) => r.staffName },
            {
              header: "Base",
              render: (r) => formatCurrency(r.baseSalary),
              align: "right",
            },
            { header: "Present", render: (r) => r.daysPresent, align: "right" },
            { header: "Absent", render: (r) => r.daysAbsent, align: "right" },
            {
              header: "Deductions",
              render: (r) => formatCurrency(r.deductions),
              align: "right",
            },
            {
              header: "Net",
              render: (r) => formatCurrency(r.netSalary),
              align: "right",
            },
            {
              header: "",
              render: (r) => (
                <button
                  type="button"
                  onClick={() => downloadSlip(r.staffId, month)}
                  disabled={isDownloading}
                  className="text-xs text-crust-600 underline"
                >
                  Generate Slip
                </button>
              ),
              align: "right",
            },
          ]}
        />
      </div>

      {preview && preview.length > 0 && (
        <div className="mt-4 flex items-center justify-between rounded-xl border border-crust-100 bg-white p-4">
          <div>
            <p className="text-sm text-crust-500">Total payout for {month}</p>
            <p className="text-xl font-semibold text-crust-900">
              {formatCurrency(totalNet)}
            </p>
          </div>
          {isSuperAdmin ? (
            <Button
              className="w-auto bg-red-600 px-5 hover:bg-red-700"
              onClick={() => setShowConfirm(true)}
              disabled={processedMonth === month}
            >
              Process &amp; Finalize
            </Button>
          ) : (
            <p className="text-xs text-crust-400">
              Only a super admin can finalize payroll.
            </p>
          )}
        </div>
      )}

      {showConfirm && (
        <ConfirmDialog
          title={`Finalize payroll for ${month}?`}
          description={
            <>
              This commits real payroll records for{" "}
              <strong>{preview?.length ?? 0} staff members</strong>, totaling{" "}
              <strong>{formatCurrency(totalNet)}</strong>. This cannot be undone
              from this screen. Double-check the preview above before
              confirming.
            </>
          }
          isDangerous
          isLoading={isProcessing}
          confirmLabel="Yes, finalize payroll"
          onConfirm={handleConfirmProcess}
          onCancel={() => setShowConfirm(false)}
        />
      )}
    </div>
  );
}
