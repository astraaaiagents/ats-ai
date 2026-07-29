import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes with conflict resolution.
 * @example cn("bg-red", "bg-blue hover:bg-green") → "bg-red hover:bg-green"
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
