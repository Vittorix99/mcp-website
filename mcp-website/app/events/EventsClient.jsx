"use client"

import { useState, useEffect, useMemo } from "react"
import EventCard from "@/components/pages/events/EventCard"
import { PageHeader } from "@/components/PageHeader"
import { Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { getAllEvents } from "@/services/events"
import { getImageUrl } from "@/config/firebaseStorage"
import { useRouter } from "next/navigation"

export default function EventsClient({ initialEvents, initialError }) {
  const [events, setEvents] = useState(() => initialEvents || [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(initialError)
  const [activeFilter, setActiveFilter] = useState("upcoming")
  const [heroImageUrl, setHeroImageUrl] = useState(null)
  const [heroLoading, setHeroLoading] = useState(false)
  const router = useRouter()

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

  const formatDate = (dateString) => {
    try {
      const [day, month, year] = dateString?.split("-").map(Number)
      return `${day.toString().padStart(2, "0")}-${month.toString().padStart(2, "0")}-${year}`
    } catch (e) {
      return dateString || "Date to be announced"
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

  const nextUpcomingEvent = useMemo(() => {
    const today = new Date()
    return sortedEvents.find((event) => parseEventDate(event.date) >= today) || null
  }, [sortedEvents])

  useEffect(() => {
    let cancelled = false
    const loadHero = async () => {
      if (!nextUpcomingEvent?.image) {
        setHeroImageUrl(null)
        return
      }
      setHeroLoading(true)
      try {
        const url = await getImageUrl("events", `${nextUpcomingEvent.image}.jpg`)
        if (!cancelled) setHeroImageUrl(url)
      } catch {
        if (!cancelled) setHeroImageUrl(null)
      } finally {
        if (!cancelled) setHeroLoading(false)
      }
    }
    loadHero()
    return () => {
      cancelled = true
    }
  }, [nextUpcomingEvent])

  const getSeason = (date) => {
    const month = date.getMonth()
    if (month <= 1 || month === 11) return "Winter"
    if (month <= 4) return "Spring"
    if (month <= 7) return "Summer"
    return "Autumn"
  }

  const groupedEvents = useMemo(() => {
    const groups = new Map()
    filteredEvents.forEach((event) => {
      const date = parseEventDate(event.date)
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`
      const label = `${date.toLocaleString("en-US", { month: "long" })} ${date.getFullYear()}`
      const season = getSeason(date)
      if (!groups.has(monthKey)) {
        groups.set(monthKey, { key: monthKey, label, season, items: [] })
      }
      groups.get(monthKey).items.push(event)
    })
    return Array.from(groups.values())
  }, [filteredEvents])

  const gridVariants = {
    hidden: {},
    show: {
      transition: { staggerChildren: 0.08 },
    },
  }

  const cardVariants = {
    hidden: { opacity: 0, y: 18 },
    show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
  }

  if (loading) {
    return (
    <div className="min-h-screen bg-black">
      <div className="container mx-auto px-4">
        <PageHeader title="ALL EVENTS" />
      </div>
      <div className="flex items-center justify-center pt-10">
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    </div>
    )
  }

  if (error) {
    return (
    <div className="min-h-screen bg-black">
      <div className="container mx-auto px-4">
        <PageHeader title="ALL EVENTS" />
      </div>
      <div className="container mx-auto px-4 md:px-6 pt-10">
        <div className="text-center text-red-500 font-helvetica">{error}</div>
      </div>
    </div>
    )
  }

  return (
    <div className="min-h-screen bg-black space-y-4 events-page">
      <div className="container mx-auto px-4">
        <PageHeader title="ALL EVENTS" />

        {activeFilter !== "past" && nextUpcomingEvent && (
          <motion.section
            className="events-hero"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="events-hero__media">
              {heroImageUrl ? (
                <img src={heroImageUrl} alt={nextUpcomingEvent.title} className="events-hero__img" />
              ) : (
                <div className="events-hero__placeholder" />
              )}
              {heroLoading && <div className="events-hero__loading" />}
            </div>
            <div className="events-hero__content">
              <p className="events-hero__eyebrow">Next Event</p>
              <h2 className="events-hero__title">{nextUpcomingEvent.title}</h2>
              <p className="events-hero__meta">{formatDate(nextUpcomingEvent.date)}</p>
              <Button
                onClick={() => router.push(`/events/${nextUpcomingEvent.slug}`)}
                className="events-hero__cta"
              >
                View Details
              </Button>
            </div>
          </motion.section>
        )}

        {/* Filtri */}
        <div className="flex justify-center mb-8 mt-10 events-page__filters">
          <div className="inline-flex bg-black/40 backdrop-blur-sm rounded-full p-1 border border-white/10">
            <button
              onClick={() => setActiveFilter("upcoming")}
              className={`font-helvetica px-4 py-2 rounded-full text-sm transition-colors ${
                activeFilter === "upcoming" ? "bg-mcp-gradient text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Upcoming
            </button>
            <button
              onClick={() => setActiveFilter("past")}
              className={`font-helvetica px-4 py-2 rounded-full text-sm transition-colors ${
                activeFilter === "past" ? "bg-mcp-gradient text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              Past
            </button>
            <button
              onClick={() => setActiveFilter("all")}
              className={`font-helvetica px-4 py-2 rounded-full text-sm transition-colors ${
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

          {groupedEvents.map((group) => (
            <section key={group.key} className="events-month">
              <div className="events-month__header">
                <h3 className="events-month__title">{group.label}</h3>
                <span className="events-month__season">{group.season}</span>
              </div>
              <motion.div
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 events-grid"
                variants={gridVariants}
                initial="hidden"
                whileInView="show"
                viewport={{ once: true, amount: 0.2 }}
              >
                {group.items.map((event) => {
                  const key = event.id || event.slug || event.title
                  return (
                    <motion.div key={key} variants={cardVariants}>
                      <EventCard event={event} />
                    </motion.div>
                  )
                })}
              </motion.div>
            </section>
          ))}
        </div>
      </div>
    </div>
  )
}
