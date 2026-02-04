"use client"

import Link from "next/link"
import { Calendar, MapPin, Clock, Loader2 } from "lucide-react"
import { getImageUrl } from "@/config/firebaseStorage"
import { routes, getRoute } from "@/config/routes"
import { useState, useEffect, useRef } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { motion } from "framer-motion"

export default function EventCard({ event, onCoverLoaded }) {
  const [imageUrl, setImageUrl] = useState(null)
  const [imageAspectRatio, setImageAspectRatio] = useState(4 / 5) // Default aspect ratio
  const [isLoading, setIsLoading] = useState(true)
  const notifiedRef = useRef(false)
  const imgRef = useRef(null)

  useEffect(() => {
    async function fetchImageUrl() {
      setIsLoading(true)
      if (event.image) {
        try {
          const url = await getImageUrl("events", `${event.image}.jpg`)
          setImageUrl(url)
        } catch (error) {
          console.error("Error loading image:", error)
          setIsLoading(false)
          if (onCoverLoaded && !notifiedRef.current) {
            notifiedRef.current = true
            onCoverLoaded(event.id || event.slug || event.title)
          }
        }
      } else {
        setIsLoading(false)
        if (onCoverLoaded && !notifiedRef.current) {
          notifiedRef.current = true
          onCoverLoaded(event.id || event.slug || event.title)
        }
      }
    }
    fetchImageUrl()
    return () => {
      notifiedRef.current = false
    }
  }, [event.image, onCoverLoaded])

  const handleImageLoad = ({ naturalWidth, naturalHeight }) => {
    setImageAspectRatio(naturalWidth / naturalHeight)
    setIsLoading(false)
    if (onCoverLoaded && !notifiedRef.current) {
      notifiedRef.current = true
      onCoverLoaded(event.id || event.slug || event.title)
    }
  }

  useEffect(() => {
    if (!imgRef.current) return
    if (!isLoading) return
    if (imgRef.current.complete) {
      handleImageLoad(imgRef.current)
    }
  }, [imageUrl, isLoading])

  // Verifica se l'evento è passato
  const isPastEvent = () => {
    try {
      const [day, month, year] = event.date.split("-").map(Number)
      const eventDate = new Date(year, month - 1, day)
      return eventDate < new Date()
    } catch (e) {
      return false
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

  const past = isPastEvent()
  const status = event.status || (past ? "ended" : "active")
  const statusLabel =
    status === "coming_soon"
      ? "Coming soon"
      : status === "sold_out"
        ? "Sold out"
        : status === "ended"
          ? "Ended"
          : null

  const publicLocation = event.locationHint || event.location || "Private Location (PA)"

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="h-full"
    >
      <Card className="bg-black border border-mcp-orange/20 overflow-hidden h-full flex flex-col">
      <CardContent className="p-0 flex flex-col flex-grow">
          <div className="relative" style={{ paddingBottom: `${(1 / imageAspectRatio) * 100}%` }}>
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
              </div>
            )}
            <img
              ref={imgRef}
              src={imageUrl || "/placeholder.svg"}
              alt={event.title}
              className="absolute inset-0 w-full h-full object-cover"
              loading="eager"
              decoding="async"
              onLoad={(e) => handleImageLoad(e.currentTarget)}
              onError={() => {
                setIsLoading(false)
                if (onCoverLoaded && !notifiedRef.current) {
                  notifiedRef.current = true
                  onCoverLoaded(event.id || event.slug || event.title)
                }
              }}
            />
            {statusLabel && (
              <div className="absolute top-3 left-3 rounded-full bg-black/70 px-3 py-1 text-xs font-semibold text-white">
                {statusLabel}
              </div>
            )}
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
                <span className="truncate">{publicLocation}</span>
              </div>
              <div className="flex items-center text-gray-300 text-sm">
                <Clock className="w-4 h-4 mr-2 text-mcp-orange flex-shrink-0" />
                <span className="truncate">
                  {event.startTime} - {event.endTime || "TILL THE END"}
                </span>
              </div>
            </div>
          </div>
          <div className="mt-auto bottom-0">

          <Link
            href={getRoute(routes.events.details, event.slug)}
            className="block w-full text-center py-3 bg-gradient-to-r from-mcp-orange to-mcp-red text-white font-bold text-sm hover:opacity-90 transition-opacity"
            >
            View Details
          </Link>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
  
  
  
}
