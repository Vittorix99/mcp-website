import { Suspense } from "react"
import { EventContent } from "./content"
import { Loader2 } from "lucide-react"
import { getAllEvents } from "@/services/events"
import { endpoints } from "@/config/endpoints"
import { getBaseUrlFromHeaders } from "@/lib/seo/base-url"

export const revalidate = 3600
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
        id: event.slug.toString(),
      }))
  } catch (error) {
    console.error("Errore nel recupero degli eventi:", error)
    return []
  }
}

async function fetchEvent(eventId) {
  if (!eventId) return null
  try {
    const key = encodeURIComponent(eventId)
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

export async function generateMetadata({ params }) {
  const { id } = params
  const event = await fetchEvent(id)
  const title = event?.title ? `${event.title} | Event Photos` : "Event Photos | Music Connecting People"
  const description = event?.date
    ? `Photo gallery from ${event.title} · ${event.date}`
    : "Browse photo galleries from Music Connecting People events."
  const baseUrl = await getBaseUrlFromHeaders()
  const canonical = baseUrl ? `${baseUrl}/events-foto/${id}` : undefined

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

export default async function EventPhotosDetailPage({ params }) {
  const { id } = await params

  if (!id) {
    return <Suspense fallback={<div>Caricamento...</div>} />
  }

  const initialEvent = await fetchEvent(id)

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
        </div>
      }
    >
      <EventContent id={id} initialEvent={initialEvent} />
    </Suspense>
  )
}
