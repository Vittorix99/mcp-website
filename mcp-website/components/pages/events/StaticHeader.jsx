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
    <motion.div className="event-meta-strip" initial="initial" animate="animate" variants={fadeInUp}>
      <Meta icon={Calendar}>{formatDate(event.date)}</Meta>
      <Meta icon={MapPin}>{event.locationHint || event.location || "Location to be announced"}</Meta>
      {event.startTime && (
        <Meta icon={Clock}>
          {event.startTime}
          {event.endTime ? ` - ${event.endTime}` : ""}
        </Meta>
      )}
    </motion.div>
  )
}

const Meta = ({ icon: Icon, children }) => (
  <div className="event-meta-strip__chip">
    <Icon className="w-4 h-4" />
    <span className="font-helvetica">{children}</span>
  </div>
)
