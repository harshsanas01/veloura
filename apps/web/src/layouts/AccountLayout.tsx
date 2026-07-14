import { Heart, LogOut, Package, User } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { useCurrentUser, useLogout } from "@/hooks/useAuth";
import { cn } from "@/utils/cn";

const LINKS = [
  { label: "Overview", to: "/account", icon: User, end: true },
  { label: "Orders", to: "/account/orders", icon: Package, end: false },
  { label: "Wishlist", to: "/account/wishlist", icon: Heart, end: false },
];

export function AccountLayout() {
  const user = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="container-veloura py-12">
      <h1 className="font-display text-3xl text-ink">My Account</h1>
      <p className="mt-1 text-sm text-ink-secondary">Welcome back, {user?.full_name}.</p>

      <div className="mt-8 grid gap-10 lg:grid-cols-[220px_1fr]">
        <aside className="flex flex-row gap-2 overflow-x-auto lg:flex-col lg:gap-1">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 whitespace-nowrap rounded px-4 py-2.5 text-sm font-medium text-ink-secondary transition-colors hover:bg-black/5",
                  isActive && "bg-rose/40 text-burgundy",
                )
              }
            >
              <link.icon className="h-4 w-4" />
              {link.label}
            </NavLink>
          ))}
          <button
            onClick={logout}
            className="flex items-center gap-2.5 whitespace-nowrap rounded px-4 py-2.5 text-left text-sm font-medium text-ink-secondary transition-colors hover:bg-black/5"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </aside>
        <div>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
