import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

export function formatFirestoreTimestamp(ts) {
  if (!ts) return "-"
  try {
    const date = ts.toDate ? ts.toDate() : new Date(ts)
    return date.toLocaleString("it-IT")
  } catch {
    return "-"
  }
}


  export function parseEventDate(dateString) {
  if (!dateString || typeof dateString !== "string") return new Date(0) // fallback

  const [day, month, year] = dateString.split("-").map(Number)

  if (!day || !month || !year) return new Date(0)

  return new Date(year, month - 1, day)
}