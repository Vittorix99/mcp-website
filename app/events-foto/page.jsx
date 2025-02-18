"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { getAllEvents } from "@/services/events"
import { getImageUrl, checkFolderExists } from "@/config/firebase"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, Camera } from "lucide-react"
import { routes, getRoute } from "@/config/routes"

const eventImageStyles = `
  .event-image-container {
    position: relative;
    width: 100%;
    padding-top: 100%; /* Square for mobile */
    overflow: hidden;
  }

  .event-image {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .event-image-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 0.75rem;
    background: linear-gradient(to top, rgba(0,0,0,0.8), rgba(0,0,0,0));
  }

  @media (min-width: 640px) {
    .event-image-container {
      padding-top: 33.33%; /* 3:1 aspect ratio for larger screens */
    }
  }
`

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
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black py-24">
        <div className="container mx-auto px-4">
          <div className="text-center text-mcp-orange text-xl">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <>
      <style jsx>{eventImageStyles}</style>
      <div className="min-h-screen bg-black mb-5 pb-16 pt-16">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold text-center gradient-text mb-12">Event Photos</h1>

          {events.length === 0 ? (
            <div className="text-center text-gray-300 text-xl">No event photos available at the moment.</div>
          ) : (
            <div className="grid grid-cols-1  lg:grid-cols-1 gap-4 sm:gap-6 mb-5">
              {events.map((event) => (
                <motion.div
                  key={event.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <Link href={getRoute(routes.events.foto.details, event.id)}>
                    <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-300">
                      <CardContent className="p-0">
                        <div className="event-image-container">
                          <img
                            src={event.coverPhoto || "/placeholder.svg"}
                            alt={`${event.title} cover`}
                            className="event-image"
                          />
                          <div className="event-image-overlay">
                            <h2 className="text-sm sm:text-base font-bold text-white line-clamp-1">{event.title}</h2>
                            <p className="text-xs text-gray-300 mt-1 flex items-center">
                              <Camera className="w-3 h-3 mr-1" />
                              View Photos
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

