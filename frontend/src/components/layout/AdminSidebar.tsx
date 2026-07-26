"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/admin/dashboard", label: "Dashboard" },
  { href: "/admin/analytics", label: "Analytics" },
  { href: "/admin/products", label: "Products" },
  { href: "/admin/categories", label: "Categories" },
  { href: "/admin/orders", label: "Orders" },
  { href: "/admin/custom-orders", label: "Custom Orders" },
  { href: "/admin/inventory", label: "Inventory" },
  { href: "/admin/coupons", label: "Coupons" },
  { href: "/admin/customers", label: "Customers" },
  { href: "/admin/staff", label: "Staff" },
  { href: "/admin/attendance", label: "Attendance" },
  { href: "/admin/salary", label: "Salary" },
  { href: "/admin/notifications", label: "Notifications" },
];

export function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-56 flex-shrink-0 border-r border-crust-100 bg-white md:block">
      <div className="p-4">
        <p className="font-display text-lg font-semibold text-crust-900">
          Admin
        </p>
      </div>
      <nav className="flex flex-col gap-0.5 px-2">
        {NAV_ITEMS.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-lg px-3 py-2 text-sm",
                active
                  ? "bg-crust-100 font-medium text-crust-900"
                  : "text-crust-600",
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
