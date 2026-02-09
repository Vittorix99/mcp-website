import { Suspense } from "react"
import { EventContent } from "./content"
import { Loader2 } from "lucide-react"
import { getAllEvents } from "@/services/events"
import { endpoints } from "@/config/endpoints"
import { getFolderPage } from "@/config/firebaseStorage"
import { getBaseUrlFromEnv } from "@/lib/seo/base-url"

export const revalidate = 3600
const PAGE_SIZE = 16
export const dynamicParams = true

export async function generateStaticParams() {
  try {
    const events = await getAllEvents({ view: "ids" })
    if (!events?.success || !events?.events?.length) {
      return []
    }
    return events.events
      .filter((event) => event?.slug)
      .map((event) => ({
        slug: event.slug.toString(),
      }))
  } catch (error) {
    console.error("Errore nel recupero degli eventi:", error)
    return []
  }
}

async function fetchEvent(eventSlug) {
  if (!eventSlug) return null
  try {
    const key = encodeURIComponent(eventSlug)
    const response = await fetch(`${endpoints.getEventById}?slug=${key}&id=${key}`, {
      cache: "force-cache",
      next: { revalidate },
    })
    if (!response.ok) return null
    return await response.json()
  } catch (error) {
    console.error("Errore nel recupero dell'evento foto:", error)
    return null
  }
}

async function fetchPagePhotos(photoPath, pageSize = PAGE_SIZE, pageIndex = 0) {
  if (!photoPath) return { totalLength: 0, pageUrls: [] }
  try {
    const folder = photoPath.startsWith("foto/") ? photoPath : `foto/${photoPath}`
    return await getFolderPage(folder, pageSize, pageIndex)
  } catch (error) {
    console.error("Errore nel recupero delle foto dell'evento:", error)
    return { totalLength: 0, pageUrls: [] }
  }
}

export async function generateMetadata({ params }) {
  const { slug } = await params
  const event = await fetchEvent(slug)
  const title = event?.title ? `${event.title} | Event Photos` : "Event Photos | Music Connecting People"
  const description = event?.date
    ? `Photo gallery from ${event.title} · ${event.date}`
    : "Browse photo galleries from Music Connecting People events."
  const baseUrl = getBaseUrlFromEnv()
  const canonical = baseUrl ? `${baseUrl}/events-foto/${slug}` : undefined

  return {
    title,
    description,
    alternates: canonical ? { canonical } : undefined,
    openGraph: {
      title,
      description,
      url: canonical,
      type: "article",
    },
  }
}

export default async function EventPhotosDetailPage({ params, searchParams }) {
  const { slug } = await params

  if (!slug) {
    return <Suspense fallback={<div>Caricamento...</div>} />
  }

  const resolvedSearchParams = await searchParams
  const pageParam = Array.isArray(resolvedSearchParams?.page)
    ? resolvedSearchParams.page[0]
    : resolvedSearchParams?.page
  const page = Math.max(1, parseInt(pageParam, 10) || 1)
  const pageIndex = page - 1

  const initialEvent = await fetchEvent(slug)
  const { totalLength, pageUrls } = await fetchPagePhotos(initialEvent?.photoPath || "", PAGE_SIZE, pageIndex)
  let nextPageUrls = []
  if ((pageIndex + 1) * PAGE_SIZE < totalLength) {
    const next = await fetchPagePhotos(initialEvent?.photoPath || "", PAGE_SIZE, pageIndex + 1)
    nextPageUrls = next.pageUrls || []
  }

  const pageImages = (pageUrls || []).map((url, index) => ({
    src: url,
    alt: `${initialEvent?.title || "Event"} - Photo ${pageIndex * PAGE_SIZE + index + 1}`,
  }))

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
        </div>
      }
    >
      <EventContent
        initialEvent={initialEvent}
        pageImages={pageImages}
        pageSize={PAGE_SIZE}
        totalLength={totalLength}
        currentPage={page}
        slug={slug}
        prefetchUrls={nextPageUrls}
      />
    </Suspense>
  )
}
