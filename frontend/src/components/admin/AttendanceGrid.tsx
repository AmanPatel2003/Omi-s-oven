import { cn } from "@/lib/utils";
import type { AttendanceReportRow, AttendanceStatus } from "@/types/api";

export const ATTENDANCE_STATUS_STYLES: Record<AttendanceStatus, string> = {
  present: "bg-green-100 text-green-700",
  absent: "bg-red-100 text-red-700",
  leave: "bg-amber-100 text-amber-700",
  holiday: "bg-gray-100 text-gray-500",
};

const ATTENDANCE_STATUS_LETTERS: Record<AttendanceStatus, string> = {
  present: "P",
  absent: "A",
  leave: "L",
  holiday: "H",
};

export function AttendanceGrid({
  rows,
  daysInMonth,
}: {
  rows: AttendanceReportRow[];
  daysInMonth: number;
}) {
  const dayNumbers = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  return (
    <div className="overflow-x-auto">
      <table className="border-separate border-spacing-1">
        <thead>
          <tr>
            <th className="sticky left-0 bg-crust-50 px-2 text-left text-xs font-medium text-crust-500">
              Staff
            </th>
            {dayNumbers.map((d) => (
              <th
                key={d}
                className="w-7 text-center text-[10px] font-medium text-crust-400"
              >
                {d}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.staffId}>
              <td className="sticky left-0 whitespace-nowrap bg-white pr-3 text-sm text-crust-800">
                {row.staffName}
              </td>
              {dayNumbers.map((d) => {
                const status = row.days[String(d)];
                return (
                  <td key={d}>
                    {status ? (
                      <span
                        title={status}
                        className={cn(
                          "flex h-6 w-6 items-center justify-center rounded text-[10px] font-semibold",
                          ATTENDANCE_STATUS_STYLES[status],
                        )}
                      >
                        {ATTENDANCE_STATUS_LETTERS[status]}
                      </span>
                    ) : (
                      <span className="flex h-6 w-6 items-center justify-center rounded bg-crust-50" />
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
