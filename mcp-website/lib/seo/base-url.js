import { headers } from "next/headers"

export async function getBaseUrlFromHeaders() {
  const h = await headers()
  const proto = h.get("x-forwarded-proto") || "https"
  const host = h.get("x-forwarded-host") || h.get("host")
  if (!host) return ""
  return `${proto}://${host}`.replace(/\/$/, "")
}
