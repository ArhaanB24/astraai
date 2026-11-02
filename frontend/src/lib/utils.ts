import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatINR(val: number | string | null | undefined, includeDecimals = true): string {
  if (val === null || val === undefined || isNaN(Number(val))) return "₹0.00";
  const num = Number(val);
  const isNegative = num < 0;
  const absVal = Math.abs(num);
  const formatted = absVal.toLocaleString("en-IN", {
    minimumFractionDigits: includeDecimals ? 2 : 0,
    maximumFractionDigits: includeDecimals ? 2 : 0,
  });
  return isNegative ? `-₹${formatted}` : `₹${formatted}`;
}

