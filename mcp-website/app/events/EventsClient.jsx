"use client"

import { useState, useEffect, useCallback } from "react"
import EventCard from "@/components/pages/events/EventCard"
import { SectionTitle } from "@/components/ui/section-title"
import { Loader2, ArrowLeft, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { useMediaQuery } from "@/hooks/useMediaQuery"
import { getAllEvents } from "@/services/events"

export default function EventsClient({ initialEvents, initialError }) {
  const [events, setEvents] = useState(() => initialEvents || [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(initialError)
  const [activeFilter, setActiveFilter] = useState("upcoming")
  const [scrollPosition, setScrollPosition] = useState(0)
  const [coverLoaded, setCoverLoaded] = useState({})
  const [coversReady, setCoversReady] = useState(false)
  const scrollAmount = 300 // Quantità di scroll per ogni click
  const isDesktop = useMediaQuery("(min-width: 1024px)")

  useEffect(() => {
    if (Array.isArray(initialEvents) && initialEvents.length > 0) return
    let cancelled = false
    setLoading(true)
    ;(async () => {
      try {
        const { success, events: fetched, error: fetchError } = await getAllEvents({ view: "card" })
        if (cancelled) return
        if (!success || !Array.isArray(fetched)) {
          setError(fetchError || "Impossibile caricare gli eventi.")
          setEvents([])
          return
        }
        setEvents(fetched)
        setError(null)
      } catch {
        if (!cancelled) setError("Errore imprevisto durante il recupero degli eventi.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [initialEvents])

  // Funzione per convertire la data nel formato "DD-MM-YYYY" in un oggetto Date
  const parseEventDate = (dateString) => {
    try {
      const [day, month, year] = dateString.split("-").map(Number)
      return new Date(year, month - 1, day)
    } catch (e) {
      return new Date(0) // Fallback a una data molto vecchia in caso di errore
    }
  }

  const sortedEvents = [...events].sort((a, b) => {
    const dateA = parseEventDate(a.date)
    const dateB = parseEventDate(b.date)
    return dateB - dateA
  })

  const filteredEvents = sortedEvents.filter((event) => {
    const eventDate = parseEventDate(event.date)
    const today = new Date()

    if (activeFilter === "upcoming") {
      return eventDate >= today
    } else if (activeFilter === "past") {
      return eventDate < today
    }
    return true // "all" filter
  })

  const handleCoverLoaded = useCallback((eventKey) => {
    setCoverLoaded((prev) => (prev[eventKey] ? prev : { ...prev, [eventKey]: true }))
  }, [])

  useEffect(() => {
    if (!filteredEvents.length) {
      setCoversReady(false)
      return
    }
    const loadedCount = filteredEvents.filter((event) => {
      const key = event.id || event.slug || event.title
      return coverLoaded[key]
    }).length
    setCoversReady(loadedCount === filteredEvents.length)
  }, [filteredEvents, coverLoaded])

  const scrollLeft = () => {
    const container = document.getElementById("events-container")
    if (container) {
      const newPosition = Math.max(0, scrollPosition - scrollAmount)
      container.scrollTo({ left: newPosition, behavior: "smooth" })
      setScrollPosition(newPosition)
    }
  }

  const scrollRight = () => {
    const container = document.getElementById("events-container")
    if (container) {
      const newPosition = scrollPosition + scrollAmount
      container.scrollTo({ left: newPosition, behavior: "smooth" })
      setScrollPosition(newPosition)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="h-24"></div>
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black">
        <div className="h-24"></div>
        <div className="container mx-auto px-4 md:px-6 pt-16">
          <div className="text-center text-red-500 font-helvetica">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black space-y-4">
      {/* Spacer div to push content below navbar */}
      <div className="h-24"></div>

      <div className="container mx-auto px-4">
        <SectionTitle as="h1" className="">
          ALL EVENTS
        </SectionTitle>

        {/* Filtri */}
        <div className="flex justify-center mb-8 mt-12 ">
          <div className="inline-flex bg-black/30 backdrop-blur-sm rounded-lg p-1">
            <button
              onClick={() => setActiveFilter("upcoming")}
              className={`font-helvetica px-4 py-2 rounded-md text-sm transition-colors ${
                activeFilter === "upcoming" ? "bg-mcp-gradient text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Upcoming
            </button>
            <button
              onClick={() => setActiveFilter("past")}
              className={`font-helvetica px-4 py-2 rounded-md text-sm transition-colors ${
                activeFilter === "past" ? "bg-mcp-gradient text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Past
            </button>
            <button
              onClick={() => setActiveFilter("all")}
              className={`font-helvetica px-4 py-2 rounded-md text-sm transition-colors ${
                activeFilter === "all" ? "bg-mcp-gradient text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              All
            </button>
          </div>
        </div>

        {/* Eventi */}
        <div className="relative">
          {activeFilter === "upcoming" && filteredEvents.length === 0 && (
            <div className="text-center text-gray-400 font-helvetica py-12">
              No upcoming events scheduled
            </div>
          )}

          {filteredEvents.length > 0 && !coversReady && (
            <div className="mt-6 flex items-center justify-center">
              <Loader2 className="w-6 h-6 text-mcp-orange animate-spin" />
            </div>
          )}

          <div className={coversReady ? "opacity-100" : "opacity-0 pointer-events-none"}>
            {isDesktop && filteredEvents.length > 0 && (
              <>
                <Button
                  onClick={scrollLeft}
                  className="absolute left-0 top-1/2 -translate-y-1/2 z-10 rounded-full w-10 h-10 p-0 bg-black/50 hover:bg-black/80"
                >
                  <ArrowLeft className="h-5 w-5" />
                </Button>
                <Button
                  onClick={scrollRight}
                  className="absolute right-0 top-1/2 -translate-y-1/2 z-10 rounded-full w-10 h-10 p-0 bg-black/50 hover:bg-black/80"
                >
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </>
            )}

            <div
              id="events-container"
              className={`grid gap-6 ${
                isDesktop
                  ? "grid-flow-col auto-cols-[minmax(300px,1fr)] overflow-x-auto pb-4 scrollbar-hide"
                  : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
              }`}
            >
              {filteredEvents.map((event) => {
                const key = event.id || event.slug || event.title
                return (
                  <motion.div
                    key={key}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <EventCard event={event} onCoverLoaded={handleCoverLoaded} />
                  </motion.div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
