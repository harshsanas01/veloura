import { Instagram, Twitter, Youtube } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { useToastStore } from "@/store/toastStore";

const COLUMNS = [
  {
    title: "Shop",
    links: [
      { label: "Women", to: "/shop/women" },
      { label: "Men", to: "/shop/men" },
      { label: "New Arrivals", to: "/shop?sort=newest" },
      { label: "AI Stylist", to: "/ai-stylist" },
    ],
  },
  {
    title: "Help",
    links: [
      { label: "Order Status", to: "/account/orders" },
      { label: "Shipping & Returns", to: "/shop" },
      { label: "Contact Us", to: "/shop" },
    ],
  },
  {
    title: "About",
    links: [
      { label: "Our Story", to: "/" },
      { label: "Sustainability", to: "/" },
      { label: "Careers", to: "/" },
    ],
  },
];

export function Footer() {
  const [email, setEmail] = useState("");
  const push = useToastStore((s) => s.push);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    push("You're on the list. Welcome to Veloura.", "success");
    setEmail("");
  }

  return (
    <footer className="border-t border-border bg-surface">
      <div className="container-veloura grid gap-12 py-16 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div className="flex flex-col gap-4">
          <span className="font-display text-2xl font-semibold text-ink">VELOURA</span>
          <p className="max-w-xs text-sm text-ink-secondary">
            Modern fashion for every occasion, styled with intelligence. Join our list for early
            access to new arrivals and edits from our AI stylist.
          </p>
          <form onSubmit={handleSubmit} className="flex max-w-sm gap-2">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Your email address"
              className="input-veloura"
            />
            <button type="submit" className="btn-primary shrink-0">
              Join
            </button>
          </form>
          <div className="mt-2 flex gap-3 text-ink-secondary">
            <Instagram className="h-4 w-4" />
            <Twitter className="h-4 w-4" />
            <Youtube className="h-4 w-4" />
          </div>
        </div>
        {COLUMNS.map((col) => (
          <div key={col.title} className="flex flex-col gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink">{col.title}</span>
            {col.links.map((link) => (
              <Link key={link.label} to={link.to} className="text-sm text-ink-secondary hover:text-ink">
                {link.label}
              </Link>
            ))}
          </div>
        ))}
      </div>
      <div className="border-t border-border py-6">
        <div className="container-veloura flex flex-col items-center justify-between gap-2 text-xs text-ink-secondary sm:flex-row">
          <span>&copy; {new Date().getFullYear()} Veloura. All rights reserved.</span>
          <span>Crafted with intelligent styling, powered by Veloura AI.</span>
        </div>
      </div>
    </footer>
  );
}
