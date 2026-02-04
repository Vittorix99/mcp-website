import { headers } from "next/headers"

async function getBaseUrl() {
  const envUrl = process.env.NEXT_PUBLIC_SITE_URL || process.env.SITE_URL
  if (envUrl) return envUrl.replace(/\/$/, "")

  const h = await headers()
  const proto = h.get("x-forwarded-proto") || "https"
  const host = h.get("x-forwarded-host") || h.get("host")
  if (!host) return "https://example.com"
  return `${proto}://${host}`
}

export async function GET() {
  const baseUrl = await getBaseUrl()
  const body = [
    "User-agent: *",
    "Disallow: /admin",
    "Disallow: /api",
    `Sitemap: ${baseUrl}/sitemap.xml`,
    "",
  ].join("\n")

  return new Response(body, {
    status: 200,
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
    },
  })
}
