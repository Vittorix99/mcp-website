import { headers } from "next/headers"

const DEFAULT_SITE_URL = "https://musiconnectingpeople.com"

export function getBaseUrlFromEnv() {
  const envUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.SITE_URL
  if (envUrl) return envUrl.replace(/\/$/, "")
  if (process.env.NODE_ENV === "production") return DEFAULT_SITE_URL
  return ""
}

export async function getBaseUrlFromHeaders() {
  const envUrl = getBaseUrlFromEnv()
  if (envUrl) return envUrl

  const h = await headers()
  const proto = h.get("x-forwarded-proto") || "https"
  const host = h.get("x-forwarded-host") || h.get("host")
  if (!host) return ""
  return `${proto}://${host}`.replace(/\/$/, "")
}
