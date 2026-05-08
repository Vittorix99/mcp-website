import { endpoints } from "@/config/endpoints"
import { getFolderPage } from "@/config/firebaseStorage"

export const dynamic = "force-dynamic"

const DEFAULT_PAGE_SIZE = 16
const MAX_PAGE_SIZE = 48

async function fetchEvent(eventSlug) {
  if (!eventSlug) return null

  try {
    const key = encodeURIComponent(eventSlug)
    const response = await fetch(`${endpoints.getEventById}?slug=${key}&id=${key}`, {
      next: { revalidate: 300 },
    })
    if (!response.ok) return null
    return await response.json()
  } catch {
    return null
  }
}

function parsePositiveInt(value, fallback) {
  const parsed = parseInt(value, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

export async function GET(request, { params }) {
  const { slug } = await params
  const url = new URL(request.url)
  const page = parsePositiveInt(url.searchParams.get("page"), 1)
  const pageSize = Math.min(
    MAX_PAGE_SIZE,
    parsePositiveInt(url.searchParams.get("pageSize"), DEFAULT_PAGE_SIZE)
  )

  const event = await fetchEvent(slug)
  const photoPath = event?.photoPath

  if (!photoPath) {
    return Response.json(
      { page, pageSize, totalLength: 0, pageUrls: [] },
      { status: event ? 200 : 404 }
    )
  }

  const folder = photoPath.startsWith("foto/") ? photoPath : `foto/${photoPath}`
  const { totalLength, pageUrls } = await getFolderPage(folder, pageSize, page - 1)

  return Response.json(
    { page, pageSize, totalLength, pageUrls },
    {
      headers: {
        "Cache-Control": "private, max-age=300",
      },
    }
  )
}
