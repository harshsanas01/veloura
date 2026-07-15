import { useEffect, useState } from "react";

const STORAGE_KEY = "veloura_recently_viewed";
const MAX_ITEMS = 8;

function read(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export function recordRecentlyViewed(slug: string): void {
  const current = read().filter((s) => s !== slug);
  current.unshift(slug);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(current.slice(0, MAX_ITEMS)));
}

export function useRecentlyViewed(excludeSlug?: string): string[] {
  const [slugs, setSlugs] = useState<string[]>([]);

  useEffect(() => {
    setSlugs(read().filter((s) => s !== excludeSlug));
  }, [excludeSlug]);

  return slugs;
}
