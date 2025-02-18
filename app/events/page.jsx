"use client"

import { useState, useEffect } from "react"

import { getAllEvents } from "@/services/events"
import EventCard from "@/components/pages/events/EventCard"


export default function AllEvents() {
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchEvents() {
      try {
        const response = await getAllEvents()
        if (response.success) {
          const sortedEvents = response.events.sort((a, b) => new Date(b.date) - new Date(a.date))
          setEvents(sortedEvents)
        } else {
          setError(response.error || "Unable to fetch events.")
        }
      } catch (err) {
        setError("An unexpected error occurred while fetching events.")
      } finally {
        setLoading(false)
      }
    }
    fetchEvents()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-black py-24">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center text-mcp-orange">Loading events...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black py-24">
        <div className="container mx-auto px-4 md:px-6">
          <div className="text-center text-red-500">{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen mt-5 bg-black py-24">
      <div className="container mt-6 mx-auto px-4 md:px-6">
        <h1 className="text-4xl  md:text-5xl font-bold text-center text-mcp-orange mb-12">All Events</h1>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          {events.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      </div>
    </div>
  )
}

