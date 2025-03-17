"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import Image from "next/image"
import Link from "next/link"
import { Calendar, Clock, MapPin, Music } from "lucide-react"
import { getImageUrl } from "@/config/firebase"
import { routes, getRoute } from "@/config/routes"

export function NextEventSection({ event }) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [imageError, setImageError] = useState(false)

  useEffect(() => {
    async function fetchNextEvent() {
      try {
        if (event) {
          const url = await getImageUrl("events", `${event.image}.jpg`)
          setImageUrl(url)
        } else {
          setError("Unable to fetch the next event.")
        }
      } catch (err) {
        setError("Unexpected error occurred while fetching the next event.")
      } finally {
        setLoading(false)
      }
    }
    fetchNextEvent()
  }, [])

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  if (loading) {
    return (
      <section className="py-24 bg-black/50 backdrop-blur-md">
        <div className="container mx-auto px-4">
          <motion.h2
            className="font-atlantico text-5xl font-extrabold text-center gradient-text uppercase mb-8"
            initial="initial"
            animate="animate"
            variants={fadeInUp}
          >
            Next Event
          </motion.h2>
          <motion.div
            className="font-helvetica text-center text-gray-300"
            initial="initial"
            animate="animate"
            variants={fadeInUp}
          >
            Loading...
          </motion.div>
        </div>
      </section>
    )
  }

  if (!event) {
    return (
      <section className="py-24 bg-black/50 backdrop-blur-md">
        <div className="container mx-auto px-4">
          <motion.h2
            className="font-atlantico text-5xl font-extrabold text-center gradient-text uppercase mb-8"
            initial="initial"
            animate="animate"
            variants={fadeInUp}
          >
            Next Event
          </motion.h2>
          <motion.div
            className="font-helvetica text-center text-gray-300"
            initial="initial"
            animate="animate"
            variants={fadeInUp}
          >
            No upcoming events scheduled
          </motion.div>
        </div>
      </section>
    )
  }

  let formattedDate = ""
  try {
    const [day, month, year] = event.date?.split("-").map(Number)
    formattedDate = `${day.toString().padStart(2, "0")}-${month.toString().padStart(2, "0")}-${year}`
  } catch (e) {
    formattedDate = event.date || "Date to be announced"
  }

  const filteredLineup = event.lineup.filter((artist) => artist.trim() !== "")

  return (
    <section className="py-24 bg-black/50 backdrop-blur-md">
      <div className="container mx-auto px-4">
        <motion.h2
          className="font-atlantico text-5xl font-extrabold text-center gradient-text uppercase mb-12"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          Next Event
        </motion.h2>
        <motion.div initial="initial" animate="animate" variants={fadeInUp}>
          <Card className="max-w-4xl mx-auto bg-black/70 border border-mcp-orange/50 overflow-hidden">
            <CardContent className="p-8">
              <div className="grid md:grid-cols-2 gap-8 items-center">
                <div className="space-y-6">
                  <h3 className="font-charter text-3xl font-bold gradient-text">{event.title}</h3>
                  <div className="font-helvetica space-y-2 text-gray-300">
                    <p className="flex items-center">
                      <Calendar className="w-5 h-5 mr-2 text-mcp-orange" />
                      {formattedDate}
                    </p>
                    <p className="flex items-center">
                      <Clock className="w-5 h-5 mr-2 text-mcp-orange" />
                      {event.startTime} - {event.endTime}
                    </p>
                    {event.location && (
                      <p className="flex items-center">
                        <MapPin className="w-5 h-5 mr-2 text-mcp-orange" />
                        {event.location}
                      </p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <p className="font-helvetica text-gray-300 flex items-center">
                      <Music className="w-5 h-5 mr-2 text-mcp-orange" />
                      Featuring:
                    </p>
                    {filteredLineup.length > 0 ? (
                      <ul className="font-helvetica list-disc list-inside text-gray-300 pl-7">
                        {filteredLineup.map((artist, index) => (
                          <li key={index}>{artist}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="font-helvetica text-gray-400 italic pl-7">No lineup available</p>
                    )}
                  </div>
                  {event.active ? (
                    <Link href={getRoute(routes.events.details, event.id)}>
                      <Button className="font-atlantico mt-5 bg-mcp-gradient hover:opacity-90 text-white font-bold py-3 px-6 rounded-md transition-all duration-300 transform hover:scale-105">
                        Tickets & Info
                      </Button>
                    </Link>
                  ) : (
                    <Button
                      className="font-helvetica bg-gray-700 cursor-not-allowed text-gray-300 font-bold py-3 px-6 rounded-md"
                      disabled
                    >
                      Coming Soon
                    </Button>
                  )}
                </div>
                <div className="aspect-square relative rounded-lg overflow-hidden">
                  {imageUrl && !imageError ? (
                    <Image
                      src={imageUrl || "/placeholder.svg"}
                      alt={event.title}
                      fill
                      className="object-cover"
                      onError={() => setImageError(true)}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-800">
                      <p className="font-helvetica text-gray-400 text-sm italic">Image not available</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  )
}

