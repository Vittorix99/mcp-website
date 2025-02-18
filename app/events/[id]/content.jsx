"use client"
import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import Image from "next/image"
import { motion } from "framer-motion"
import { MapPin, Calendar, Clock, Info } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { getEventById } from "@/services/events"
import { getImageUrl } from "@/config/firebase"
import { PayPalSection } from "@/components/pages/events/PayPalSection"
import { Loader2 } from "lucide-react"


export function EventContent({id}) {
  
    const [event, setEvent] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [imageUrl, setImageUrl] = useState(null)
    const [imageLoading, setImageLoading] = useState(true)
    
  
    const splitBrText = (text) => {
      const processedText = text.replace(/\\n/g, "\n")
      return processedText.split("\n")
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
        <div className="min-h-screen bg-black py-24">
          <div className="container mx-auto px-4">
            <div className="text-center gradient-text">Loading...</div>
          </div>
        </div>
      )
    }
  
    if (error || !event) {
      return (
        <div className="min-h-screen bg-black py-24">
          <div className="container mx-auto px-4">
            <Alert className="bg-mcp-orange/10 border-mcp-orange/20">
              <AlertDescription className="text-white text-center text-lg">
                {error || "Event currently unavailable"}
              </AlertDescription>
            </Alert>
          </div>
        </div>
      )
    }
  
    let formattedDate = ""
    try {
      const [day, month, year] = event.date?.split("-").map(Number)
      formattedDate = `${day.toString().padStart(2, "0")}-${month.toString().padStart(2, "0")}-${year}`
    } catch (e) {
      formattedDate = event.date || "Date to be announced"
    }
  
    const fadeInUp = {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      transition: { duration: 0.6 },
    }
  
    return (
      <div className="min-h-screen py-24 bg-black relative">
        <div className="container mx-auto px-4">
          <motion.div className="text-center mb-12" initial="initial" animate="animate" variants={fadeInUp}>
            <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-4">{event.title || "Event"}</h1>
            <div className="flex justify-center gap-6 text-gray-300 text-sm">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-mcp-orange" />
                <span>{formattedDate}</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-mcp-orange" />
                <span>{event.location || "Location to be announced"}</span>
              </div>
              {event.startTime && event.endTime && (
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-mcp-orange" />
                  <span>
                    {event.startTime} - {event.endTime}
                  </span>
                </div>
              )}
            </div>
          </motion.div>
  
          <div className="grid lg:grid-cols-2 px-4 md:px-12 lg:px-24 gap-12 mx-auto  lg:max-w-6xl">
            <motion.div className="space-y-6" initial="initial" animate="animate" variants={fadeInUp}>
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
            </motion.div>
  
            <motion.div initial="initial" animate="animate" variants={fadeInUp}>
              <Card className="bg-black/50 border  md:max-w-2xl border-mcp-orange/50">
                <CardContent className="p-6 space-y-6">
                  {event.price && (
                    <div className="text-center">
                      <div className="text-3xl font-bold gradient-text">{event.price}€</div>
                      <div className="text-gray-300 text-sm">Current price</div>
                    </div>
                  )}
  
                  {event.note && (
                    <div className="space-y-4 text-sm">
                      {splitBrText(event.note).map((line, index) => (
                        <div key={index} className="text-gray-300 flex items-start">
                          <Info className="w-4 h-4 text-mcp-orange mr-2 mt-1 flex-shrink-0" />
                          <span style={{ whiteSpace: "pre-wrap" }}>{line}</span>
                        </div>
                      ))}
                    </div>
                  )}
  
                  <div className="mt-6">
                    {event.active ? (
                      <PayPalSection event={event} />
                    ) : (
                      <div className="text-center text-gray-300 text-sm">Tickets not available</div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    )
  }