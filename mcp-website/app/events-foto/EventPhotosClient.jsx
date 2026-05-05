"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { getImageUrl } from "@/config/firebaseStorage"
import { routes, getRoute } from "@/config/routes"
import { parseEventDate } from "@/lib/utils"
import { getAllEvents } from "@/services/events"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const FALLBACK_BG = ["#1a0e06", "#06060f", "#0f0508", "#0c0c02", "#020810", "#100407"]

function formatDate(dateString) {
  try {
    const [day, month, year] = (dateString || "").split("-").map(Number)
    return `${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}.${year}`
  } catch {
    return dateString || ""
  }
}

function EventCoverCard({ ev, index }) {
  const [hov, setHov] = useState(false)
  const href = getRoute(routes.events.foto.details, ev.slug)
  const bg = FALLBACK_BG[index % FALLBACK_BG.length]

  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      onClick={() => window.location.href = href}
      style={{
        position: "relative", aspectRatio: "4/3",
        background: bg, cursor: "pointer", overflow: "hidden",
      }}
    >
      {/* Cover photo */}
      {ev.coverPhoto && (
        <img
          src={ev.coverPhoto}
          alt={ev.title}
          style={{
            position: "absolute", inset: 0, width: "100%", height: "100%",
            objectFit: "cover",
            transform: hov ? "scale(1.04)" : "scale(1)",
            transition: "transform 0.5s ease",
          }}
        />
      )}

      {/* Texture */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none",
        backgroundImage: `repeating-linear-gradient(45deg,
          rgba(255,255,255,0.012) 0px,rgba(255,255,255,0.012) 1px,
          transparent 1px,transparent 18px)`,
      }} />

      {/* Hover overlay */}
      <div style={{
        position: "absolute", inset: 0,
        background: "rgba(0,0,0,0.45)",
        opacity: hov ? 1 : 0,
        transition: "opacity 0.3s ease",
      }} />

      {/* Accent top border */}
      <div style={{
        position: "absolute", top: 0, left: 0, right: 0, height: "3px",
        background: ACC, opacity: hov ? 1 : 0.4, transition: "opacity 0.3s",
      }} />

      {/* Placeholder label when no photo */}
      {!ev.coverPhoto && (
        <div style={{
          position: "absolute", inset: 0, display: "flex",
          alignItems: "center", justifyContent: "center",
          fontFamily: HN, fontSize: "8px",
          letterSpacing: "0.25em", textTransform: "uppercase",
          color: "rgba(245,243,239,0.12)",
        }}>cover photo</div>
      )}

      {/* Bottom info */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        padding: "40px 24px 24px",
        background: "linear-gradient(to top, rgba(0,0,0,0.9), transparent)",
        transition: "transform 0.3s ease",
        transform: hov ? "translateY(0)" : "translateY(8px)",
      }}>
        <p style={{
          fontFamily: CH, fontSize: "12px",
          fontStyle: "italic", color: "rgba(245,243,239,0.45)",
          marginBottom: "4px",
        }}>{formatDate(ev.date)}</p>
        <h3 style={{
          fontFamily: HN, fontWeight: 900, fontSize: "22px",
          letterSpacing: "-0.02em", textTransform: "uppercase",
          color: "#F5F3EF", marginBottom: "8px",
        }}>{ev.title}</h3>
        <p style={{
          fontFamily: HN, fontSize: "9px",
          letterSpacing: "0.2em", textTransform: "uppercase",
          color: hov ? ACC : "rgba(245,243,239,0.3)",
          transition: "color 0.3s",
        }}>View photos →</p>
      </div>
    </div>
  )
}

export default function EventPhotosClient({ initialEvents, initialError }) {
  const [rawEvents, setRawEvents] = useState(() => initialEvents || [])
  const [events, setEvents] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(initialError)

  useEffect(() => {
    if (Array.isArray(rawEvents) && rawEvents.length > 0) return
    let cancelled = false
    setLoading(true)
    ;(async () => {
      try {
        const { success, events: fetched, error: fetchError } = await getAllEvents({ view: "gallery" })
        if (cancelled) return
        if (!success || !Array.isArray(fetched)) {
          setError(fetchError || "Unable to load events.")
          setRawEvents([])
          return
        }
        setRawEvents(fetched)
      } catch {
        if (!cancelled) setError("An error occurred.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [rawEvents])

  useEffect(() => {
    if (!Array.isArray(rawEvents) || rawEvents.length === 0) return
    let cancelled = false

    ;(async () => {
      setLoading(true)
      try {
        const withCovers = await Promise.all(
          rawEvents.map(async (ev) => {
            try {
              const folder = ev.photoPath ? `foto/${ev.photoPath}` : ev.title ? `foto/${ev.title}` : null
              if (!folder) return { ...ev, coverPhoto: null, hasPhotos: false }
              const url = await getImageUrl(folder, "cover.jpg")
              return { ...ev, coverPhoto: url, hasPhotos: Boolean(url) }
            } catch {
              return { ...ev, coverPhoto: null, hasPhotos: false }
            }
          })
        )
        if (cancelled) return
        const sorted = withCovers
          .filter(e => e.hasPhotos)
          .sort((a, b) => parseEventDate(b.date) - parseEventDate(a.date))
        setEvents(sorted)
        setError(null)
      } catch {
        if (!cancelled) setError("Unable to load event photos.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()

    return () => { cancelled = true }
  }, [rawEvents])

  return (
    <div style={{ minHeight: "100svh", background: "#080808", paddingTop: "100px" }}>
      <div style={{ padding: "40px 40px 52px" }}>
        <Link href="/" style={{
          fontFamily: HN, fontSize: "9px", letterSpacing: "0.32em",
          textTransform: "uppercase", color: "rgba(245,243,239,0.35)",
          textDecoration: "none", display: "block", marginBottom: "28px",
        }}>← Back</Link>
        <h1 style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(48px,10vw,120px)", letterSpacing: "-0.04em",
          textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.84,
          marginBottom: "12px",
        }}>Photos</h1>
        <p style={{
          fontFamily: CH, fontSize: "15px",
          fontStyle: "italic", color: "rgba(245,243,239,0.35)",
        }}>Every event, documented.</p>
      </div>

      {loading && (
        <div style={{ padding: "0 40px 80px" }}>
          <p style={{ fontFamily: HN, fontSize: "11px", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(245,243,239,0.3)" }}>
            Loading…
          </p>
        </div>
      )}

      {error && (
        <div style={{ padding: "0 40px 80px" }}>
          <p style={{ fontFamily: CH, fontSize: "14px", color: "#D10000" }}>{error}</p>
        </div>
      )}

      {!loading && !error && events.length === 0 && (
        <div style={{ padding: "0 40px 80px" }}>
          <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>
            No event photos available yet.
          </p>
        </div>
      )}

      {!loading && events.length > 0 && (
        <div style={{
          padding: "0 40px 80px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(320px,1fr))",
          gap: "2px",
        }}>
          {events.map((ev, i) => (
            <EventCoverCard key={ev.id || ev.slug || i} ev={ev} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
