import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  sublabel,
  className,
}: {
  label: string;
  value: string;
  sublabel?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-crust-100 bg-white p-4",
        className,
      )}
    >
      <p className="text-xs text-crust-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-crust-900">{value}</p>
      {sublabel && <p className="mt-1 text-xs text-crust-500">{sublabel}</p>}
    </div>
  );
}
