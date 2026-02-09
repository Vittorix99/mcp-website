import { headers } from "next/headers"
import { getAllEvents } from "@/services/events"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

async function getBaseUrl() {
  const envUrl = getBaseUrlFromEnv()
  if (envUrl) return envUrl.replace(/\/$/, "")

  const h = await headers()
  const proto = h.get("x-forwarded-proto") || "https"
  const host = h.get("x-forwarded-host") || h.get("host")
  if (!host) return "https://example.com"
  return `${proto}://${host}`
}

function xmlEscape(str) {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&apos;")
}

function buildUrl(loc, lastmod) {
  const parts = [`<loc>${xmlEscape(loc)}</loc>`]
  if (lastmod) parts.push(`<lastmod>${lastmod}</lastmod>`)
  return `<url>${parts.join("")}</url>`
}

export async function GET() {
  const baseUrl = await getBaseUrl()
  const now = new Date().toISOString()

  const urls = [
    buildUrl(`${baseUrl}/`, now),
    buildUrl(`${baseUrl}/events`, now),
    buildUrl(`${baseUrl}/events-foto`, now),
  ]

  try {
    const eventsRes = await getAllEvents({ view: "ids" })
    const events = eventsRes?.events || []
    events.forEach((event) => {
      const slug = event?.slug
      if (!slug) return
      urls.push(buildUrl(`${baseUrl}/events/${slug}`, now))
      urls.push(buildUrl(`${baseUrl}/events-foto/${slug}`, now))
    })
  } catch {
    // keep base URLs only
  }

  const body = `<?xml version="1.0" encoding="UTF-8"?>` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">` +
    `${urls.join("")}</urlset>`

  return new Response(body, {
    status: 200,
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
    },
  })
}
