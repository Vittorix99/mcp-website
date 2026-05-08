"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const FALLBACK_BG = ["#1a0e06", "#06060f", "#0f0508", "#0c0c02", "#020810", "#100407"]
const EAGER_COVER_COUNT = 8

function formatDate(dateString) {
  try {
    const [day, month, year] = (dateString || "").split("-").map(Number)
    return `${String(day).padStart(2, "0")}.${String(month).padStart(2, "0")}.${year}`
  } catch {
    return dateString || ""
  }
}

function preloadImage(src) {
  return new Promise((resolve) => {
    if (!src || typeof window === "undefined") {
      resolve()
      return
    }

    const img = new window.Image()
    img.decoding = "async"
    img.onload = () => {
      if (typeof img.decode === "function") {
        img.decode().catch(() => {}).finally(resolve)
        return
      }
      resolve()
    }
    img.onerror = resolve
    img.src = src
  })
}

function EventCoverCard({ ev, index }) {
  const [hov, setHov] = useState(false)
  const href = `/events-foto/${ev.slug}`
  const bg = FALLBACK_BG[index % FALLBACK_BG.length]
  const isEager = index < EAGER_COVER_COUNT

  return (
    <Link
      href={href}
      prefetch={false}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        position: "relative", aspectRatio: "4/3",
        background: bg, cursor: "pointer", overflow: "hidden",
        display: "block", textDecoration: "none",
        contentVisibility: isEager ? "visible" : "auto",
        containIntrinsicSize: "360px 270px",
      }}
    >
      {/* Cover photo */}
      {ev.coverPhoto && (
        <img
          src={ev.coverPhoto}
          alt={ev.title}
          loading={isEager ? "eager" : "lazy"}
          fetchPriority={isEager ? "high" : "low"}
          decoding="async"
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
    </Link>
  )
}

function CoverGridSkeleton({ count = EAGER_COVER_COUNT }) {
  const items = Array.from({ length: Math.max(1, count) })

  return (
    <div style={{
      padding: "0 40px 80px",
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(320px,1fr))",
      gap: "2px",
    }}>
      {items.map((_, index) => (
        <div
          key={index}
          style={{
            aspectRatio: "4/3",
            background: FALLBACK_BG[index % FALLBACK_BG.length],
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{
            position: "absolute",
            inset: 0,
            backgroundImage: `repeating-linear-gradient(45deg,
              rgba(255,255,255,0.012) 0px,rgba(255,255,255,0.012) 1px,
              transparent 1px,transparent 18px)`,
          }} />
          <div style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: 0,
            height: "42%",
            background: "linear-gradient(to top, rgba(0,0,0,0.75), transparent)",
          }} />
        </div>
      ))}
    </div>
  )
}

export default function EventPhotosClient({ initialEvents, initialError }) {
  const [events, setEvents] = useState(() => Array.isArray(initialEvents) ? initialEvents : [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(initialError || null)
  const [coversReady, setCoversReady] = useState(false)
  const fetchedRef = useRef(false)
  const hasServerPayloadRef = useRef(Array.isArray(initialEvents) && !initialError)

  useEffect(() => {
    if (events.length > 0 || fetchedRef.current || hasServerPayloadRef.current) return

    fetchedRef.current = true
    let cancelled = false
    setLoading(true)
    setError(null)

    ;(async () => {
      try {
        const response = await fetch("/api/event-photo-albums", { cache: "force-cache" })
        const data = await response.json().catch(() => ({}))
        if (cancelled) return

        if (!response.ok || !Array.isArray(data.events)) {
          setError(data.error || "Unable to load event photos.")
          setEvents([])
          return
        }

        setEvents(data.events)
      } catch {
        if (!cancelled) setError("Unable to load event photos.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()

    return () => { cancelled = true }
  }, [events.length])

  useEffect(() => {
    if (!events.length) {
      setCoversReady(true)
      return
    }

    let cancelled = false
    setCoversReady(false)

    const coverUrls = events
      .slice(0, EAGER_COVER_COUNT)
      .map((event) => event.coverPhoto)
      .filter(Boolean)

    if (!coverUrls.length) {
      setCoversReady(true)
      return
    }

    Promise.allSettled(coverUrls.map(preloadImage)).then(() => {
      if (!cancelled) setCoversReady(true)
    })

    return () => { cancelled = true }
  }, [events])

  const showCoverSkeleton = loading || (!error && events.length > 0 && !coversReady)

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

      {showCoverSkeleton && <CoverGridSkeleton count={Math.min(events.length || EAGER_COVER_COUNT, EAGER_COVER_COUNT)} />}

      {!loading && error && (
        <div style={{ padding: "0 40px 80px" }}>
          <p style={{ fontFamily: CH, fontSize: "14px", color: "#D10000" }}>{error}</p>
        </div>
      )}

      {!loading && !error && coversReady && events.length === 0 && (
        <div style={{ padding: "0 40px 80px" }}>
          <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>
            No event photos available yet.
          </p>
        </div>
      )}

      {!loading && !error && coversReady && events.length > 0 && (
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
