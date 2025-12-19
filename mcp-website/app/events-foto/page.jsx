"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { getAllEvents } from "@/services/events"
import { getImageUrl } from "@/config/firebaseStorage"
import { Loader2, Camera, Calendar } from "lucide-react"
import { routes, getRoute } from "@/config/routes"
import { SectionTitle } from "@/components/ui/section-title"
import { AnimatedSectionDivider } from "@/components/AnimatedSectionDivider"
import { parseEventDate } from "@/lib/utils" // se l'hai definita

export default function EventPhotosPage() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [coverLoaded, setCoverLoaded] = useState({})

useEffect(() => {
  const fetchEvents = async () => {
    try {
      const { success, events, error } = await getAllEvents({ view: "gallery" })

      if (!success || !Array.isArray(events)) {
        console.error("[fetchEvents] Fallito il recupero eventi")
        setError(error || "Impossibile recuperare gli eventi.")
        return
      }

      const eventsWithPhotos = await Promise.all(
        events.map(async (event) => {
          const folder = event.photoPath || event.title ? `foto/${event.photoPath || event.title}` : null
          if (!folder) {
            return { ...event, coverPhoto: null, hasPhotos: false }
          }
          const coverPhotoUrl = await getImageUrl(folder, "cover.jpg")
          return { ...event, coverPhoto: coverPhotoUrl, hasPhotos: Boolean(coverPhotoUrl) }
        })
      )

      const sortedEvents = eventsWithPhotos
        .filter((e) => e.hasPhotos)
        .sort((a, b) => parseEventDate(b.date) - parseEventDate(a.date))

      setEvents(sortedEvents)
    } catch (err) {
      setError("Errore durante il caricamento degli eventi.")
    } finally {
      setLoading(false)
    }
  }

  fetchEvents()
}, [])



  const formatDate = (dateString) => {
    try {
      const [day, month, year] = dateString?.split("-").map(Number)
      return `${day.toString().padStart(2, "0")}-${month.toString().padStart(2, "0")}-${year}`
    } catch (e) {
      return dateString || "Data da definire"
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-12 md:pt-24 mt-6 md:mt-16">
        <Loader2 className="w-5 h-5 md:w-8 md:h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black py-12 md:py-24 pt-20 md:pt-40">
        <div className="container mx-auto px-3 md:px-4">
          <div className="text-center text-mcp-orange text-sm md:text-xl font-helvetica">{error}</div>
        </div>
      </div>
    )
  }

  // Format date function


  return (
    <div className="min-h-screen bg-black">
      {/* Spacer div to push content below navbar */}
      <div className="h-24 "></div>

      <div className="container mx-auto px-4">
        <SectionTitle as="h1" className="mt-8 md:mt-8 text-2xl md:text-5xl">
          Event Photos
        </SectionTitle>


        {events.length === 0 ? (
          <div className="text-center text-gray-300 text-sm md:text-xl font-helvetica py-8">
            No event photos available at the moment.
          </div>
        ) : (
          <div className="space-y-6 md:space-y-16 mb-8 md:mb-12">
            {events.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="px-1 md:px-0"
              >
                <Link href={getRoute(routes.events.foto.details, event.id)}>
                  <div className="group">
                    <div className="grid md:grid-cols-2 gap-3 md:gap-6 items-center">
                      <div className="relative aspect-video overflow-hidden rounded-lg">
                        <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent z-10" />
                        {event.coverPhoto ? (
                          <>
                            <img
                              src={event.coverPhoto || "/placeholder.svg"}
                              alt={event.title}
                              className={`w-full h-full object-cover transition duration-500 group-hover:scale-105 ${
                                coverLoaded[event.id] ? "opacity-100" : "opacity-0 scale-105"
                              }`}
                              onLoad={() =>
                                setCoverLoaded((prev) => ({ ...prev, [event.id]: true }))
                              }
                              onError={(e) => {
                                e.target.onerror = null
                                e.target.src = "/placeholder.svg"
                              }}
                            />
                            {!coverLoaded[event.id] && (
                              <div className="absolute inset-0 bg-zinc-900 animate-pulse" />
                            )}
                          </>
                        ) : (
                          <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                            <Camera className="w-6 h-6 md:w-12 md:h-12 text-gray-600" />
                          </div>
                        )}
                        <div className="absolute bottom-1.5 md:bottom-4 left-1.5 md:left-4 z-20">
                          <div className="inline-flex items-center">
                            <Camera className="w-3.5 h-3.5 md:w-5 md:h-5 text-white" />
                          </div>
                        </div>
                      </div>

                      <div className="space-y-1.5 md:space-y-4 mt-1.5 md:mt-0 flex flex-col items-center text-center">
                        <div>
                          <h2 className="font-charter text-lg md:text-2xl font-bold text-white group-hover:text-orange-500 transition-colors line-clamp-2">
                            {event.title}
                          </h2>
                          <div className="font-helvetica text-xs md:text-sm text-gray-300 flex items-center justify-center mt-1 md:mt-2">
                            <Calendar className="w-3 h-3 md:w-4 md:h-4 mr-1 md:mr-2 text-mcp-orange flex-shrink-0" />
                            {formatDate(event.date)}
                          </div>
                        </div>
                        {event.description && (
                          <p className="font-helvetica text-xs md:text-sm text-gray-400 line-clamp-2 md:line-clamp-3 mt-2 md:mt-3">
                            {event.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>

                {index < events.length - 1 && (
                  <div className="mt-4 mb-4 md:mt-8 md:mb-8">
                    <hr className="border-gray-800" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
