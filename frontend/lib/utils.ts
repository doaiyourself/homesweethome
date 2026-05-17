import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatMan(amount: number | null | undefined): string {
  if (!amount) return "-";
  if (amount >= 10000) {
    const eok = Math.floor(amount / 10000);
    const man = amount % 10000;
    return man === 0 ? `${eok}억` : `${eok}억 ${man.toLocaleString()}`;
  }
  return amount.toLocaleString();
}

export function formatPrice(
  trade: string | null,
  deposit: number | null,
  monthly: number | null,
  display?: string | null,
): string {
  const base = display ?? formatMan(deposit);
  if (monthly) return `${base}/${monthly}`;
  return base;
}

export const TRADE_LABELS: Record<string, string> = {
  B1: "전세",
  B2: "월세",
  A1: "매매",
  B3: "단기",
};
