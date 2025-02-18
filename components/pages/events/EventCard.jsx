"use client"

import Link from "next/link"
import Image from "next/image"
import { Card, CardContent } from "@/components/ui/card"
import { Calendar, MapPin, Clock, Loader2 } from "lucide-react"
import { motion } from "framer-motion"
import { getImageUrl } from "@/config/firebase"
import { routes, getRoute } from "@/config/routes"
import { useState, useEffect } from "react"

export default function EventCard({ event }) {
  const [imageUrl, setImageUrl] = useState(null)
  const [imageAspectRatio, setImageAspectRatio] = useState(16 / 9)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function fetchImageUrl() {
      setIsLoading(true)
      if (event.image) {
        try {
          const url = await getImageUrl("events", `${event.image}.jpg`)
          setImageUrl(url)
        } catch (error) {
          console.error("Error loading image:", error)
        }
      }
    }
    fetchImageUrl()
  }, [event.image])

  const handleImageLoad = ({ naturalWidth, naturalHeight }) => {
    setImageAspectRatio(naturalWidth / naturalHeight)
    setIsLoading(false)
  }

  const formatDate = (dateString) => {
    const [day, month, year] = dateString.split("-").map(Number)
    return `${day.toString().padStart(2, "0")}-${month.toString().padStart(2, "0")}-${year}`
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="h-full"
    >
      <Card className="bg-black border border-mcp-orange/20 overflow-hidden h-full flex flex-col">
        <CardContent className="p-0 flex-grow">
          <div className="relative" style={{ paddingBottom: `${(1 / imageAspectRatio) * 100}%` }}>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
              </div>
            )}
            <Image
              src={imageUrl || "/placeholder.svg"}
              alt={event.title}
              layout="fill"
              objectFit="cover"
              onLoadingComplete={handleImageLoad}
              onError={() => setIsLoading(false)}
            />
          </div>
          <div className="p-4 space-y-3 flex-grow">
            <h3 className="text-xl font-bold text-mcp-orange line-clamp-2">{event.title}</h3>
            <div className="space-y-2">
              <div className="flex items-center text-gray-300 text-sm">
                <Calendar className="w-4 h-4 mr-2 text-mcp-orange flex-shrink-0" />
                <span>{formatDate(event.date)}</span>
              </div>
              <div className="flex items-center text-gray-300 text-sm">
                <MapPin className="w-4 h-4 mr-2 text-mcp-orange flex-shrink-0" />
                <span className="truncate">{event.location || "Private Location (PA)"}</span>
              </div>
              <div className="flex items-center text-gray-300 text-sm">
                <Clock className="w-4 h-4 mr-2 text-mcp-orange flex-shrink-0" />
                <span className="truncate">
                  {event.startTime} - {event.endTime || "TILL THE END"}
                </span>
              </div>
            </div>
          </div>
          <Link
            href={getRoute(routes.events.details, event.id)}
            className="block w-full text-center py-3 bg-gradient-to-r from-mcp-orange to-mcp-red text-white font-bold text-sm hover:opacity-90 transition-opacity"
          >
            View Details
          </Link>
        </CardContent>
      </Card>
    </motion.div>
  )
}

