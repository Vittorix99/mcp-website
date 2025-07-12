"use client"

import { motion } from "framer-motion"
import { Calendar, MapPin, Clock } from "lucide-react"

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 },
}

const formatDate = (d) => {
  try {
    const [day, month, year] = d.split("-").map(Number)
    return `${String(day).padStart(2, "0")}-${String(month).padStart(2, "0")}-${year}`
  } catch {
    return d || "Date to be announced"
  }
}

export default function StaticHeader({ event }) {
  return (
    <>
      {/* NAVBAR spacer già gestito dal wrapper */}
      <div className="container mx-auto px-4 pt-12">
        {/* Title */}
        <motion.h1
          className="font-atlantico tracking-atlantico-wide text-4xl md:text-5xl text-center text-mcp-orange mb-6"
          initial="initial" animate="animate" variants={fadeInUp}
        >
          {event.title || "Event"}
        </motion.h1>

        {/* Meta info (date – place – time) */}
        <motion.div
          className="flex flex-wrap justify-center gap-6 mb-12"
          initial="initial" animate="animate" variants={fadeInUp}
        >
          <Meta icon={Calendar}>{formatDate(event.date)}</Meta>

          <Meta icon={MapPin}>{event.location || "Location to be announced"}</Meta>

          {event.startTime && (
            <Meta icon={Clock}>
              {event.startTime}
              {event.endTime ? ` - ${event.endTime}` : ""}
            </Meta>
          )}
        </motion.div>
      </div>
    </>
  )
}

const Meta = ({ icon: Icon, children }) => (
  <div className="flex items-center text-mcp-orange">
    <Icon className="w-5 h-5 mr-2" />
    <span className="font-helvetica">{children}</span>
  </div>
)