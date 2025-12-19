"use client"

import { useState, useEffect } from "react"
import { getAllEvents } from "@/services/events"
import EventCard from "@/components/pages/events/EventCard"
import { SectionTitle } from "@/components/ui/section-title"
import { Loader2, ArrowLeft, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { motion } from "framer-motion"
import { useMediaQuery } from "@/hooks/useMediaQuery"

export default function AllEvents() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeFilter, setActiveFilter] = useState("upcoming")
  const [scrollPosition, setScrollPosition] = useState(0)
  const scrollAmount = 300 // Quantità di scroll per ogni click
  const isDesktop = useMediaQuery("(min-width: 1024px)")

useEffect(() => {
  const fetchEvents = async () => {
    try {
      const { success, events, error } = await getAllEvents({ view: "card" })

      if (!success || !events) {
        setError(error || "Impossibile caricare gli eventi.")
        return
      }

      const sorted = events.sort((a, b) => {
        const dateA = parseEventDate(a.date)
        const dateB = parseEventDate(b.date)
        return dateB - dateA
      })

      setEvents(sorted)
    } catch (e) {
      setError("Errore imprevisto durante il recupero degli eventi.")
    } finally {
      setLoading(false)
    }
  }

  fetchEvents()
}, [])
  // Funzione per convertire la data nel formato "DD-MM-YYYY" in un oggetto Date
  const parseEventDate = (dateString) => {
    try {
      const [day, month, year] = dateString.split("-").map(Number)
      return new Date(year, month - 1, day)
    } catch (e) {
      return new Date(0) // Fallback a una data molto vecchia in caso di errore
    }
  }

  const filteredEvents = events.filter((event) => {
    const eventDate = parseEventDate(event.date)
    const today = new Date()

    if (activeFilter === "upcoming") {
      return eventDate >= today
    } else if (activeFilter === "past") {
      return eventDate < today
    }
    return true // "all" filter
  })

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

        {filteredEvents.length === 0 ? (
          <div className="text-center text-gray-300 font-helvetica py-12">No {activeFilter} events available.</div>
        ) : (
          <div className="max-w-6xl mx-auto mb-12">
            {/* Layout diverso per mobile e desktop */}
            {isDesktop ? (
              // Layout desktop con scroll orizzontale
              <div className="relative">
                {/* Controlli di navigazione */}
                <div className="absolute -left-4 top-1/2 transform -translate-y-1/2 z-10">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="bg-black/50 backdrop-blur-sm text-white rounded-full h-10 w-10"
                    onClick={scrollLeft}
                  >
                    <ArrowLeft className="h-5 w-5" />
                  </Button>
                </div>

                <div className="absolute -right-4 top-1/2 transform -translate-y-1/2 z-10">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="bg-black/50 backdrop-blur-sm text-white rounded-full h-10 w-10"
                    onClick={scrollRight}
                  >
                    <ArrowRight className="h-5 w-5" />
                  </Button>
                </div>

                {/* Container orizzontale scrollabile */}
                <div
                  id="events-container"
                  className="flex overflow-x-auto pb-4 mb-12 scrollbar-hide snap-x"
                  style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
                >
                  {filteredEvents.map((event, index) => (
                    <motion.div
                      key={event.id}
                      className="flex-shrink-0 w-64 mx-3 first:ml-0 last:mr-0 snap-start"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                    >
                      <EventCard event={event} />
                    </motion.div>
                  ))}
                </div>
              </div>
            ) : (
              // Layout mobile con griglia
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-6 mb-12">
                {filteredEvents.map((event, index) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: index * 0.1 }}
                  >
                    <EventCard event={event} />
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
