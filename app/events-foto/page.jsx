"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { getAllEvents } from "@/services/events"
import { getImageUrl, checkFolderExists } from "@/config/firebase"
import { Loader2, Camera, Calendar } from "lucide-react"
import { routes, getRoute } from "@/config/routes"
import { SectionTitle } from "@/components/ui/section-title"
import { AnimatedSectionDivider } from "@/components/AnimatedSectionDivider"

export default function EventPhotosPage() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchEvents() {
      try {
        const response = await getAllEvents()
        if (response.success) {
          const eventsWithPhotos = await Promise.all(
            response.events.map(async (event) => {
              try {
                const folderExists = await checkFolderExists(`foto/${event.title}`)
                if (folderExists) {
                  const coverPhotoUrl = await getImageUrl(`foto/${event.title}/`, "cover.jpg")
                  return { ...event, coverPhoto: coverPhotoUrl, hasPhotos: true }
                }
                return { ...event, coverPhoto: null, hasPhotos: false }
              } catch (error) {
                console.error(`Error checking photos for ${event.title}:`, error)
                return { ...event, coverPhoto: null, hasPhotos: false }
              }
            }),
          )
          setEvents(eventsWithPhotos.filter((event) => event.hasPhotos))
        } else {
          setError("Unable to retrieve events.")
        }
      } catch (err) {
        setError("An error occurred while fetching events.")
      } finally {
        setLoading(false)
      }
    }
    fetchEvents()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-24 mt-16">
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black py-24 pt-40">
        <div className="container mx-auto px-4">
          <div className="text-center text-mcp-orange text-xl font-helvetica">{error}</div>
        </div>
      </div>
    )
  }

  // Format date function
  const formatDate = (dateString) => {
    try {
      const [day, month, year] = dateString?.split("-").map(Number)
      return `${day.toString().padStart(2, "0")}-${month.toString().padStart(2, "0")}-${year}`
    } catch (e) {
      return dateString || "Date to be announced"
    }
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Spacer div to push content below navbar */}
      <div className=""></div>

      <div className="container mx-auto px-4 pt-16">
        <SectionTitle as="h1" className="mt-8">
          Event Photos
        </SectionTitle>

        <AnimatedSectionDivider color="ORANGE" className="mb-12" />

        {events.length === 0 ? (
          <div className="text-center text-gray-300 text-xl font-helvetica">
            No event photos available at the moment.
          </div>
        ) : (
          <div className="space-y-16">
            {events.map((event, index) => (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Link href={getRoute(routes.events.foto.details, event.id)}>
                  <div className="group">
                    <div className="grid md:grid-cols-2 gap-6 items-center">
                      <div className="relative aspect-video overflow-hidden rounded-lg">
                        <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent z-10" />
                        {event.coverPhoto ? (
                          <img
                            src={event.coverPhoto || "/placeholder.svg"}
                            alt={event.title}
                            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                            onError={(e) => {
                              e.target.onerror = null
                              e.target.src = "/placeholder.svg"
                            }}
                          />
                        ) : (
                          <div className="w-full h-full bg-gray-800 flex items-center justify-center">
                            <Camera className="w-12 h-12 text-gray-600" />
                          </div>
                        )}
                        <div className="absolute bottom-4 left-4 z-20">
                          <div className="inline-flex items-center">
                            <Camera className="w-5 h-5 text-white" />
                          </div>
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h2 className="font-charter text-2xl font-bold text-white group-hover:text-orange-500 transition-colors">
                          {event.title}
                        </h2>
                        <div className="font-helvetica text-sm text-gray-300 flex items-center">
                          <Calendar className="w-4 h-4 mr-2 text-mcp-orange" />
                          {formatDate(event.date)}
                        </div>
                        {event.description && (
                          <p className="font-helvetica text-gray-400 line-clamp-3">{event.description}</p>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>

                {index < events.length - 1 && (
                  <div className="mt-8 mb-8">
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

