"use client"

import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import { getAllEvents } from "@/services/events"
import { routes, getRoute } from "@/config/routes"
import { useReveal } from "@/hooks/useReveal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

function parseEventDate(dateString) {
  try {
    const [day, month, year] = (dateString || "").split("-").map(Number)
    return new Date(year, month - 1, day)
  } catch {
    return new Date(0)
  }
}

function formatEventDate(dateString) {
  try {
    const [day, month, year] = (dateString || "").split("-").map(Number)
    return `${day.toString().padStart(2, "0")}.${month.toString().padStart(2, "0")}.${year}`
  } catch {
    return dateString || ""
  }
}

function EventRow({ ev, index }) {
  const [hov, setHov] = useState(false)
  const eventHref = getRoute(routes.events.details, ev.slug)
  const today = new Date()
  const eventDate = parseEventDate(ev.date)
  const isPast = eventDate < today
  const isActive = ev.status === "active" || (!isPast && ev.status !== "soon")
  const isSoon = ev.status === "soon"

  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        display: "grid", gridTemplateColumns: "72px 1fr auto",
        gap: "28px", alignItems: "center",
        padding: `28px 0 28px ${hov ? "18px" : "0"}`,
        borderBottom: "1px solid rgba(245,243,239,0.06)",
        borderLeft: hov ? `3px solid ${ACC}` : "3px solid transparent",
        background: hov ? "rgba(224,120,0,0.025)" : "transparent",
        cursor: "pointer", transition: "all 0.2s",
      }}
      onClick={() => window.location.href = eventHref}
    >
      <p style={{ fontFamily: HN, fontSize: "11px", fontWeight: 700, color: ACC, letterSpacing: "0.1em", margin: 0 }}>
        {String(index + 1).padStart(2, "0")}
      </p>
      <div>
        <h3 style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(18px,3vw,34px)", letterSpacing: "-0.02em",
          textTransform: "uppercase",
          color: hov ? "#F5F3EF" : "rgba(245,243,239,0.82)",
          transition: "color 0.2s", margin: 0,
        }}>{ev.title}</h3>
        <div style={{ display: "flex", gap: "20px", marginTop: "6px", flexWrap: "wrap" }}>
          <span style={{ fontFamily: CH, fontSize: "13px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>
            {formatEventDate(ev.date)}
          </span>
          {ev.location && (
            <span style={{ fontFamily: HN, fontSize: "10px", letterSpacing: "0.1em", color: "rgba(245,243,239,0.28)", textTransform: "uppercase" }}>
              {ev.location}
            </span>
          )}
          {ev.lineup?.length > 0 && (
            <span style={{ fontFamily: HN, fontSize: "11px", color: "rgba(245,243,239,0.25)" }}>
              {ev.lineup.filter(a => a.trim()).join(", ")}
            </span>
          )}
        </div>
      </div>
      {isActive && !isPast ? (
        <Link
          href={eventHref}
          onClick={e => e.stopPropagation()}
          style={{
            padding: "11px 26px", background: ACC, borderRadius: "2px",
            fontFamily: HN, fontWeight: 700, fontSize: "9px",
            letterSpacing: "0.26em", textTransform: "uppercase",
            color: "#fff", textDecoration: "none", whiteSpace: "nowrap",
            display: "inline-block",
          }}
        >Tickets →</Link>
      ) : isSoon ? (
        <span style={{
          fontFamily: HN, fontSize: "8px", fontWeight: 700,
          letterSpacing: "0.26em", textTransform: "uppercase",
          color: "rgba(245,243,239,0.28)",
          border: "1px solid rgba(245,243,239,0.12)",
          padding: "10px 18px", whiteSpace: "nowrap",
        }}>Coming Soon</span>
      ) : (
        <Link
          href={eventHref}
          onClick={e => e.stopPropagation()}
          style={{
            padding: "11px 26px", background: "transparent",
            border: "1px solid rgba(245,243,239,0.14)", borderRadius: "2px",
            fontFamily: HN, fontWeight: 400, fontSize: "9px",
            letterSpacing: "0.2em", textTransform: "uppercase",
            color: "rgba(245,243,239,0.38)", textDecoration: "none",
            whiteSpace: "nowrap", display: "inline-block",
          }}
        >View Details</Link>
      )}
    </div>
  )
}

const FILTERS = ["upcoming", "past", "all"]

export default function EventsClient({ initialEvents, initialError }) {
  useReveal()
  const [events, setEvents] = useState(() => initialEvents || [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(initialError)
  const [activeFilter, setActiveFilter] = useState("upcoming")

  useEffect(() => {
    if (Array.isArray(initialEvents) && initialEvents.length > 0) return
    let cancelled = false
    setLoading(true)
    ;(async () => {
      try {
        const { success, events: fetched, error: fetchError } = await getAllEvents({ view: "card" })
        if (cancelled) return
        if (!success || !Array.isArray(fetched)) { setError(fetchError || "Unable to load events."); setEvents([]); return }
        setEvents(fetched)
        setError(null)
      } catch {
        if (!cancelled) setError("An error occurred.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [initialEvents])

  const sorted = useMemo(() =>
    [...events].sort((a, b) => parseEventDate(b.date) - parseEventDate(a.date)),
    [events]
  )

  const filtered = useMemo(() => {
    const today = new Date()
    if (activeFilter === "upcoming") return sorted.filter(e => parseEventDate(e.date) >= today)
    if (activeFilter === "past") return sorted.filter(e => parseEventDate(e.date) < today)
    return sorted
  }, [sorted, activeFilter])

  return (
    <div style={{ minHeight: "100svh", background: "#080808", paddingTop: "100px" }}>
      <div style={{ padding: "40px 40px 0" }}>
        <h1 style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(48px,10vw,120px)", letterSpacing: "-0.04em",
          textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.84,
          marginBottom: "40px",
        }}>All Events</h1>

        {/* Tab filters */}
        <div style={{ display: "flex", gap: 0, marginBottom: "52px", borderBottom: "1px solid rgba(245,243,239,0.07)" }}>
          {FILTERS.map(f => (
            <button key={f} onClick={() => setActiveFilter(f)} style={{
              background: "none", border: "none", cursor: "pointer",
              fontFamily: HN, fontSize: "10px",
              fontWeight: activeFilter === f ? 700 : 400,
              letterSpacing: "0.28em", textTransform: "uppercase",
              color: activeFilter === f ? ACC : "rgba(245,243,239,0.32)",
              padding: "12px 24px 16px",
              borderBottom: activeFilter === f ? `2px solid ${ACC}` : "2px solid transparent",
              marginBottom: "-1px", transition: "all 0.2s",
            }}>{f}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: "0 40px 80px" }}>
        {loading && (
          <p style={{ fontFamily: HN, fontSize: "11px", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(245,243,239,0.3)" }}>
            Loading…
          </p>
        )}
        {error && (
          <p style={{ fontFamily: CH, fontSize: "14px", color: "#D10000" }}>{error}</p>
        )}
        {!loading && !error && filtered.length === 0 && (
          <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>
            No events found.
          </p>
        )}
        {filtered.map((ev, i) => (
          <EventRow key={ev.id || ev.slug || i} ev={ev} index={i} />
        ))}
      </div>
    </div>
  )
}
