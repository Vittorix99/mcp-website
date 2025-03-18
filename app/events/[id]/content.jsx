"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { motion } from "framer-motion"
import { MapPin, Calendar, Clock, Circle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { getEventById } from "@/services/events"
import { getImageUrl } from "@/config/firebase"
import { PayPalSection } from "@/components/pages/events/PayPalSection"
import { Loader2 } from "lucide-react"

export function EventContent({ id }) {
  const [event, setEvent] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [imageLoading, setImageLoading] = useState(true)

  const splitBrText = (text) => {
    if (!text) return []
    const processedText = text.replace(/\\n/g, "\n")
    return processedText.split("\n").filter((line) => line.trim() !== "")
  }

  useEffect(() => {
    async function fetchEvent() {
      if (!id) {
        setError("No event ID provided")
        setLoading(false)
        return
      }
      try {
        const response = await getEventById(id)
        if (response?.success && response?.event) {
          setEvent(response.event)
          if (response.event.image) {
            const url = await getImageUrl("events", `${response.event.image}.jpg`)
            setImageUrl(url)
          }
        } else {
          setError(response?.error || "Unable to retrieve event details.")
        }
      } catch (err) {
        setError("Event currently unavailable")
      } finally {
        setLoading(false)
      }
    }
    fetchEvent()
  }, [id])

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="h-24"></div>
        <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="min-h-screen bg-black">
        <div className="h-24"></div>
        <div className="container mx-auto px-4 pt-16">
          <Alert className="bg-mcp-orange/10 border-mcp-orange/20">
            <AlertDescription className="text-white text-center text-lg font-helvetica">
              {error || "Event currently unavailable"}
            </AlertDescription>
          </Alert>
        </div>
      </div>
    )
  }

  const formatDate = (dateString) => {
    try {
      const [day, month, year] = dateString?.split("-").map(Number)
      return `${day.toString().padStart(2, "0")}-${month.toString().padStart(2, "0")}-${year}`
    } catch (e) {
      return dateString || "Date to be announced"
    }
  }

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  const noteItems = splitBrText(event.note)

  return (
    <div className="min-h-screen bg-black">
      {/* Spacer div to push content below navbar */}
      <div className="h-24"></div>

      <div className="container mx-auto px-4 pt-16">
        {/* Event Title */}
        <motion.h1
          className="font-atlantico tracking-atlantico-wide text-4xl md:text-5xl text-center text-mcp-orange mb-6"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          {event.title || "Event"}
        </motion.h1>

        {/* Event Meta Info */}
        <motion.div
          className="flex flex-wrap justify-center gap-6 mb-12"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          <div className="flex items-center text-mcp-orange">
            <Calendar className="w-5 h-5 mr-2" />
            <span className="font-helvetica">{formatDate(event.date)}</span>
          </div>

          <div className="flex items-center text-mcp-orange">
            <MapPin className="w-5 h-5 mr-2" />
            <span className="font-helvetica">{event.location || "Location to be announced"}</span>
          </div>

          {event.startTime && (
            <div className="flex items-center text-mcp-orange">
              <Clock className="w-5 h-5 mr-2" />
              <span className="font-helvetica">
                {event.startTime}
                {event.endTime ? ` - ${event.endTime}` : ""}
              </span>
            </div>
          )}
        </motion.div>

        {/* Main Content */}
        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          {/* Left Column - Event Image */}
          <div className="relative rounded-lg overflow-hidden">
              {imageLoading && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                    <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
                  </div>
                )}
                {imageUrl ? (
                  <Image
                    src={imageUrl || "/placeholder.svg"}
                    alt={event.title || "Event image"}
                    sizes="(max-width: 768px) 100vw, 33vw"
                    width={500}
                    height={200}
                    style={{ objectFit: "contain" }}
                    onLoadingComplete={() => setImageLoading(false)}
                    className="mx-auto"
                  />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
                    <p className="text-gray-400 text-sm italic">Image not available</p>
                  </div>
                )}
              </div>
          {/* Right Column - Event Details */}
          <motion.div
            initial="initial"
            animate="animate"
            variants={fadeInUp}
            className="bg-black/30 backdrop-blur-sm rounded-lg border border-mcp-orange/20 p-6"
          >
            {/* Price */}
            {event.price && (
              <div className="text-center mb-8">
                <div className="font-atlantico tracking-atlantico-wide text-4xl text-mcp-orange">{event.price}€</div>
                <div className="font-helvetica text-sm text-gray-400">Current price</div>
              </div>
            )}

            {/* Event Notes */}
            <div className="space-y-4">
              {noteItems.map((line, index) => (
                <div key={index} className="flex">
                  <Circle className="w-3 h-3 text-mcp-orange mt-1 mr-3 flex-shrink-0" fill="#FF6B00" />
                  <span className="font-helvetica text-gray-300 text-sm">{line}</span>
                </div>
              ))}

              {/* Empty lines for spacing */}
              {noteItems.length > 0 && (
                <div className="flex">
                  <Circle className="w-3 h-3 text-transparent mt-1 mr-3 flex-shrink-0" />
                  <span className="font-helvetica text-transparent text-sm">&nbsp;</span>
                </div>
              )}

              {/* Event Description */}
              {event.description && (
                <>
                  <div className="flex">
                    <Circle className="w-3 h-3 text-mcp-orange mt-1 mr-3 flex-shrink-0" fill="#FF6B00" />
                    <span className="font-helvetica text-gray-300 text-sm">{event.description}</span>
                  </div>

                  <div className="flex">
                    <Circle className="w-3 h-3 text-transparent mt-1 mr-3 flex-shrink-0" />
                    <span className="font-helvetica text-transparent text-sm">&nbsp;</span>
                  </div>
                </>
              )}

              {/* Additional Event Details */}
              {event.details &&
                splitBrText(event.details).map((line, index) => (
                  <div key={`detail-${index}`} className="flex">
                    <Circle className="w-3 h-3 text-mcp-orange mt-1 mr-3 flex-shrink-0" fill="#FF6B00" />
                    <span className="font-helvetica text-gray-300 text-sm">{line}</span>
                  </div>
                ))}
            </div>

            {/* PayPal Section */}
            <div className="mt-8">
              {event.active ? (
                <PayPalSection event={event} />
              ) : (
                <div className="text-center font-helvetica text-gray-300 text-sm py-4">Tickets not available</div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}

