"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import Image from "next/image"
import Link from "next/link"
import { Calendar, Clock, MapPin, Music } from "lucide-react"
import { getImageUrl } from "@/config/firebaseStorage"
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
  }, [event])

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  if (loading) {
    return (
      <section className="py-12 md:py-24 md:bg-black/50 md:backdrop-blur-md">
        <div className="container mx-auto px-3 md:px-4">
          <motion.h2
            className="font-atlantico text-3xl md:text-5xl font-extrabold text-center gradient-text uppercase mb-4 md:mb-8"
            initial="initial"
            animate="animate"
            variants={fadeInUp}
          >
            Next Event
          </motion.h2>
          <motion.div
            className="font-helvetica text-center text-gray-300 text-sm md:text-base"
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
      <section className="py-12 md:py-24 md:bg-black/50 md:backdrop-blur-md">
        <div className="container mx-auto px-3 md:px-4">
          <motion.h2
            className="font-atlantico text-3xl md:text-5xl font-extrabold text-center gradient-text uppercase mb-4 md:mb-8"
            initial="initial"
            animate="animate"
            variants={fadeInUp}
          >
            Next Event
          </motion.h2>
          <motion.div
            className="font-helvetica text-center text-gray-300 text-sm md:text-base"
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
    formattedDate = `${day.toString().padStart(2, "0")}-${month
      .toString()
      .padStart(2, "0")}-${year}`
  } catch (e) {
    formattedDate = event.date || "Date to be announced"
  }

  const filteredLineup = event.lineup.filter((artist) => artist.trim() !== "")
  const publicLocation = event.locationHint || event.location

  return (
    <section className="py-12 md:py-24 md:bg-black/50 md:backdrop-blur-md relative">
      <div className="container mx-auto px-3 md:px-4 relative z-10 pt-6 md:pt-16">
        <motion.h2
          className="font-atlantico text-3xl md:text-5xl text-center text-orange-500 uppercase mb-6 md:mb-12"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          Next Event
        </motion.h2>

        <motion.div initial="initial" animate="animate" variants={fadeInUp}>
          <Card className="max-w-4xl mx-auto bg-black/70 border border-mcp-orange/50 overflow-hidden">
            <CardContent className="p-4 md:p-8">
              <div className="grid md:grid-cols-2 gap-6 md:gap-8 items-center">
                <div className="space-y-4 md:space-y-6 order-2 md:order-1">
                  <h3 className="font-charter text-2xl md:text-3xl font-bold gradient-text">
                    {event.title}
                  </h3>

                  <div className="font-helvetica space-y-1.5 md:space-y-2 text-gray-300 text-sm md:text-base">
                    <p className="flex items-center">
                      <Calendar className="w-4 h-4 md:w-5 md:h-5 mr-1.5 md:mr-2 text-mcp-orange" />
                      {formattedDate}
                    </p>
                    <p className="flex items-center">
                      <Clock className="w-4 h-4 md:w-5 md:h-5 mr-1.5 md:mr-2 text-mcp-orange" />
                      {event.startTime} - {event.endTime}
                    </p>
    {publicLocation && (
                      <p className="flex items-center">
                        <MapPin className="w-4 h-4 md:w-5 md:h-5 mr-1.5 md:mr-2 text-mcp-orange" />
                        {publicLocation}
                      </p>
                    )}
                  </div>

                  <div className="space-y-1.5 md:space-y-2">
                    <p className="font-helvetica text-gray-300 flex items-center text-sm md:text-base">
                      <Music className="w-4 h-4 md:w-5 md:h-5 mr-1.5 md:mr-2 text-mcp-orange" />
                      Featuring:
                    </p>
                    {filteredLineup.length > 0 ? (
                      <ul className="font-helvetica list-disc list-inside text-gray-300 pl-5 md:pl-7 text-xs md:text-base">
                        {filteredLineup.map((artist, index) => (
                          <li key={index}>{artist}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="font-helvetica text-gray-400 italic pl-5 md:pl-7 text-xs md:text-base">
                        No lineup available
                      </p>
                    )}
                  </div>

                  {event.active ? (
                    <Link
                      href={getRoute(routes.events.details, event.id)}
                      className="block w-full"
                    >
                      <Button className="font-atlantico tracking-wider mt-3 md:mt-5 bg-mcp-gradient hover:opacity-90 text-white py-2 md:py-3 px-6 md:px-8 rounded-md transition-all duration-300 transform hover:scale-105 uppercase text-sm md:text-base h-12 md:h-14 w-full">
                        Tickets & Info
                      </Button>
                    </Link>
                  ) : (
                    <Button
                      className="font-helvetica bg-gray-700 cursor-not-allowed text-gray-300 font-bold py-2 md:py-3 px-6 md:px-8 rounded-md text-sm md:text-base h-12 md:h-14 w-full mt-3 md:mt-5"
                      disabled
                    >
                      Coming Soon
                    </Button>
                  )}
                </div>

                <div className="w-full">
                  {imageUrl && !imageError ? (
                    <Image
                      src={imageUrl}
                      alt={event.title}
                      width={800}
                      height={500}
                      className="rounded-lg w-full h-auto"
                      onError={() => setImageError(true)}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gray-800">
                      <p className="font-helvetica text-gray-400 text-xs md:text-sm italic">
                        Image not available
                      </p>
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
