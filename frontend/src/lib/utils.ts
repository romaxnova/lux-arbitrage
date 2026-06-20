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
