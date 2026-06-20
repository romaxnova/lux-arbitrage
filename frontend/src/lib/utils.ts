import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatEur(value: number) {
  return new Intl.NumberFormat("en-EU", { style: "currency", currency: "EUR" }).format(value);
}

export function formatPct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function recColor(rec: string) {
  if (rec === "BUY") return "text-buy bg-buy/10 border-buy/30";
  if (rec === "WATCH") return "text-watch bg-watch/10 border-watch/30";
  return "text-skip bg-skip/10 border-skip/30";
}

/**
 * Route a remote marketplace image through our edge image proxy so it renders
 * reliably (see /api/img). Pass-through for already-proxied or empty values.
 */
export function proxyImg(url?: string | null): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("/api/img")) return url;
  if (!/^https?:\/\//.test(url)) return undefined;
  return `/api/img?url=${encodeURIComponent(url)}`;
}

/** First usable, proxied image from a list of candidate URLs. */
export function firstImage(...lists: (string[] | undefined)[]): string | undefined {
  for (const list of lists) {
    if (!list) continue;
    for (const u of list) {
      const p = proxyImg(u);
      if (p) return p;
    }
  }
  return undefined;
}
