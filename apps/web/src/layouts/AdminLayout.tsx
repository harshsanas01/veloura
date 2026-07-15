import { LayoutGrid, MessageSquareText, Package, Receipt, Tag, Users } from "lucide-react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { Toaster } from "@/components/ui/Toaster";
import { cn } from "@/utils/cn";

const LINKS = [
  { label: "Overview", to: "/admin", icon: LayoutGrid, end: true },
  { label: "Products", to: "/admin/products", icon: Package, end: false },
  { label: "Orders", to: "/admin/orders", icon: Receipt, end: false },
  { label: "Customers", to: "/admin/customers", icon: Users, end: false },
  { label: "Coupons", to: "/admin/coupons", icon: Tag, end: false },
  { label: "Reviews", to: "/admin/reviews", icon: MessageSquareText, end: false },
];

export function AdminLayout() {
  return (
    <div className="min-h-screen bg-background">
      <div className="flex">
        <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-surface px-4 py-6 lg:flex">
          <Link to="/" className="mb-8 px-2 font-display text-xl text-ink">
            VELOURA <span className="text-xs font-sans font-medium text-ink-secondary">Admin</span>
          </Link>
          <nav className="flex flex-col gap-1">
            {LINKS.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                end={link.end}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2.5 rounded px-3 py-2.5 text-sm font-medium text-ink-secondary hover:bg-black/5",
                    isActive && "bg-rose/40 text-burgundy",
                  )
                }
              >
                <link.icon className="h-4 w-4" />
                {link.label}
              </NavLink>
            ))}
          </nav>
          <Link to="/" className="mt-auto px-3 text-xs text-ink-secondary hover:text-ink">
            &larr; Back to store
          </Link>
        </aside>
        <div className="min-w-0 flex-1 px-5 py-8 sm:px-8 lg:px-10">
          <Outlet />
        </div>
      </div>
      <Toaster />
    </div>
  );
}
