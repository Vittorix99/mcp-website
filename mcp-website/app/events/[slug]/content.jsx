"use client"

import { useEffect, useState, Suspense } from "react"
import Link from "next/link"
import Image from "next/image"
import { EVENT_CONTENT_COMPONENT, resolvePurchaseMode } from "@/config/events-utils"
import { analytics } from "@/config/firebase"
import { getImageUrl } from "@/config/firebaseStorage"
import { logEvent } from "firebase/analytics"
import PaymentWarningModal from "@/components/popups/PaymentWarningModal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const TABS = ["info", "lineup", "photos", "join"]

const HOW_TO_JOIN = [
  ["01", "Buy participation", "Complete the purchase on this page."],
  ["02", "Check your email", "Your membership card arrives as a Wallet pass."],
  ["03", "Get directions", "The exact location is revealed in your confirmation."],
  ["04", "Show up", "Scan your card at the door. That's it."],
]

function formatDateDisplay(dateString) {
  try {
    const [day, month, year] = (dateString || "").split("-").map(Number)
    const d = new Date(year, month - 1, day)
    return d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })
  } catch {
    return dateString || ""
  }
}


function EventHero({ event, imageUrl }) {
  return (
    <div className="event-detail-hero" style={{
      position: "relative", height: "68vh", minHeight: "480px",
      background: "#0f0a05", overflow: "hidden",
    }}>
      {/* Texture */}
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `repeating-linear-gradient(-45deg,
          rgba(224,120,0,0.03) 0px,rgba(224,120,0,0.03) 1px,
          transparent 1px,transparent 18px)`,
      }} />
      {/* Orange left ambient */}
      <div style={{
        position: "absolute", inset: 0,
        background: `radial-gradient(ellipse at 20% 60%, ${ACC}18 0%, transparent 55%)`,
      }} />
      {/* Orange right ambient — behind poster */}
      {imageUrl && (
        <div style={{
          position: "absolute", inset: 0,
          background: "radial-gradient(ellipse at 88% 35%, rgba(224,120,0,0.14) 0%, transparent 52%)",
          pointerEvents: "none",
        }} />
      )}
      {/* Bottom gradient */}
      <div style={{
        position: "absolute", inset: 0,
        background: "linear-gradient(to bottom, rgba(8,8,8,0.15) 0%, rgba(8,8,8,0.72) 75%, #080808 100%)",
      }} />
      {/* Top accent bar */}
      <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "3px", background: ACC }} />

      {/* ── POSTER — desktop, right side, natural aspect ratio ── */}
      {imageUrl && (
        <div className="event-hero-poster-wrap" style={{
          position: "absolute", right: "48px",
          top: "56%", transform: "translateY(-50%)",
          zIndex: 2, maxWidth: "min(36vw, 320px)", width: "100%",
        }}>
          {/* Orange glow behind poster */}
          <div style={{
            position: "absolute", inset: "-32px",
            background: "radial-gradient(ellipse at center, rgba(224,120,0,0.22) 0%, transparent 68%)",
            pointerEvents: "none", zIndex: -1,
          }} />
          <Image
            src={imageUrl}
            alt={event?.title || "Event poster"}
            width={480}
            height={600}
            priority
            sizes="(max-width: 768px) 0px, 320px"
            style={{
              width: "100%", height: "auto", display: "block",
              filter: "drop-shadow(-20px 8px 56px rgba(0,0,0,0.9))",
            }}
          />
          {/* Left fade — blends poster into hero */}
          <div style={{
            position: "absolute", top: 0, left: 0, bottom: 0, width: "45%",
            background: "linear-gradient(to right, #0f0a05, transparent)",
            pointerEvents: "none",
          }} />
          {/* Bottom fade */}
          <div style={{
            position: "absolute", left: 0, right: 0, bottom: 0, height: "28%",
            background: "linear-gradient(to top, #080808, transparent)",
            pointerEvents: "none",
          }} />
        </div>
      )}

      {/* ── BACK LINK — positioned below fixed nav ── */}
      <Link href="/events" className="event-hero-back" style={{
        position: "absolute", top: "88px", left: "48px", zIndex: 5,
        fontFamily: HN, fontSize: "9px", letterSpacing: "0.32em",
        textTransform: "uppercase", color: "rgba(245,243,239,0.38)",
        textDecoration: "none",
      }}>← All Events</Link>

      {/* ── MAIN TEXT — bottom-left ── */}
      <div className="event-detail-hero-content" style={{
        position: "absolute", bottom: "13%", left: 0, right: 0,
        padding: "0 48px", zIndex: 3,
      }}>
        {/* Mobile poster — shown only on mobile */}
        {imageUrl && (
          <div className="event-hero-mobile-poster">
            <Image
              src={imageUrl}
              alt={event?.title || "Event poster"}
              width={720}
              height={900}
              priority
              sizes="(max-width: 767px) calc(100vw - 32px), 1px"
              style={{ width: "100%", height: "100%", objectFit: "contain", display: "block" }}
            />
          </div>
        )}

        <p style={{
          fontFamily: CH, fontSize: "14px", fontStyle: "italic",
          color: "rgba(245,243,239,0.45)", marginBottom: "10px",
        }}>{formatDateDisplay(event?.date)}</p>
        <h1 className="event-hero-title" style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(36px,6vw,84px)", letterSpacing: "-0.035em",
          textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.88, margin: 0,
        }}>{event?.title}</h1>
      </div>
    </div>
  )
}

function InfoTab({ event }) {
  const location = event?.locationHint || event?.location
  const timeStr = event?.startTime ? `${event.startTime}${event.endTime ? ` — ${event.endTime}` : ""}` : null

  const metaItems = [
    ["Date", formatDateDisplay(event?.date)],
    timeStr ? ["Time", timeStr] : null,
    location ? ["Area", location] : null,
    ["Location", "Exact address revealed after purchase"],
  ].filter(Boolean)

  return (
    <div>
      <p style={{
        fontFamily: HN, fontSize: "8px", fontWeight: 700,
        letterSpacing: "0.35em", textTransform: "uppercase",
        color: ACC, marginBottom: "16px",
      }}>Event info</p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "28px", maxWidth: "680px" }}>
        {metaItems.map(([k, v]) => (
          <div key={k}>
            <p style={{
              fontFamily: HN, fontSize: "8px", fontWeight: 700,
              letterSpacing: "0.32em", textTransform: "uppercase",
              color: ACC, marginBottom: "6px",
            }}>{k}</p>
            <p style={{
              fontFamily: HN, fontSize: "14px",
              color: "rgba(245,243,239,0.65)", letterSpacing: "0.02em",
            }}>{v}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function JoinTab() {
  return (
    <div style={{ maxWidth: "600px" }}>
      <p style={{
        fontFamily: HN, fontSize: "8px", fontWeight: 700,
        letterSpacing: "0.35em", textTransform: "uppercase",
        color: ACC, marginBottom: "32px",
      }}>How to join</p>
      {HOW_TO_JOIN.map(([n, t, b]) => (
        <div key={n} style={{
          display: "grid", gridTemplateColumns: "36px 1fr", gap: "14px",
          paddingBottom: "24px", marginBottom: "24px",
          borderBottom: "1px solid rgba(245,243,239,0.05)",
        }}>
          <p style={{ fontFamily: HN, fontSize: "11px", fontWeight: 700, color: ACC, margin: 0 }}>{n}</p>
          <div>
            <p style={{
              fontFamily: HN, fontWeight: 700, fontSize: "13px",
              textTransform: "uppercase", letterSpacing: "0.04em",
              color: "#F5F3EF", marginBottom: "6px",
            }}>{t}</p>
            <p style={{
              fontFamily: CH, fontSize: "14px",
              lineHeight: 1.65, color: "rgba(245,243,239,0.45)", margin: 0,
            }}>{b}</p>
          </div>
        </div>
      ))}
      <Image
        src="/tessera-mockup.png"
        alt="Tessera MCP"
        width={180}
        height={113}
        style={{
          width: "100%", maxWidth: "180px", display: "block", margin: "32px auto 0",
          borderRadius: "10px", opacity: 0.85,
          filter: "drop-shadow(0 12px 32px rgba(0,0,0,0.7))",
        }}
      />
    </div>
  )
}

function LineupTab({ event }) {
  const lineup = event?.lineup?.filter(a => a?.trim?.()) || []

  if (lineup.length === 0) {
    return (
      <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>
        Lineup to be announced.
      </p>
    )
  }

  return (
    <div style={{ maxWidth: "680px" }}>
      <p style={{
        fontFamily: HN, fontSize: "8px", fontWeight: 700,
        letterSpacing: "0.35em", textTransform: "uppercase",
        color: ACC, marginBottom: "40px",
      }}>Artists</p>
      {lineup.map((artist, i) => {
        const name = typeof artist === "string" ? artist : artist?.name || ""
        const role = typeof artist === "object" ? artist?.role : null
        return (
          <div key={i} style={{
            display: "flex", alignItems: "baseline", justifyContent: "space-between",
            padding: "24px 0",
            borderBottom: "1px solid rgba(245,243,239,0.06)",
          }}>
            <div style={{ display: "flex", gap: "24px", alignItems: "baseline" }}>
              <span style={{
                fontFamily: HN, fontSize: "11px", fontWeight: 700,
                color: ACC, minWidth: "28px",
              }}>{String(i + 1).padStart(2, "0")}</span>
              <span style={{
                fontFamily: HN, fontWeight: 900,
                fontSize: i === 0 ? "36px" : "26px",
                letterSpacing: "-0.02em", textTransform: "uppercase",
                color: i === 0 ? "#F5F3EF" : "rgba(245,243,239,0.7)",
              }}>{name}</span>
            </div>
            {role && (
              <span style={{
                fontFamily: CH, fontSize: "13px",
                fontStyle: "italic", color: "rgba(245,243,239,0.35)",
              }}>{role}</span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function PhotosTab({ event }) {
  const photoCount = Number(event?.photosCount || 0)
  const hasPhotos = Boolean(event?.photosReady || photoCount > 0)
  const galleryHref = `/events-foto/${event?.slug}`

  return (
    <div>
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        marginBottom: "32px", flexWrap: "wrap", gap: "16px",
      }}>
        <p style={{
          fontFamily: HN, fontSize: "8px", fontWeight: 700,
          letterSpacing: "0.35em", textTransform: "uppercase",
          color: ACC, margin: 0,
        }}>From the Night</p>
        {hasPhotos && (
          <Link href={galleryHref} style={{
            background: "none", border: "1px solid rgba(245,243,239,0.15)",
            padding: "8px 18px",
            fontFamily: HN, fontSize: "9px",
            letterSpacing: "0.22em", textTransform: "uppercase",
            color: "rgba(245,243,239,0.45)", borderRadius: "2px",
            textDecoration: "none",
          }}>View Full Gallery →</Link>
        )}
      </div>

      {hasPhotos ? (
        <div style={{ textAlign: "center", paddingTop: "40px" }}>
          <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.45)", marginBottom: "24px" }}>
            {photoCount > 0 ? `${photoCount} photos from this event are available in the gallery.` : "Photos from this event are available in the gallery."}
          </p>
          <Link href={galleryHref} style={{
            display: "inline-block", padding: "13px 36px",
            background: ACC, borderRadius: "2px",
            fontFamily: HN, fontWeight: 700, fontSize: "10px",
            letterSpacing: "0.26em", textTransform: "uppercase",
            color: "#fff", textDecoration: "none",
          }}>Open Gallery →</Link>
        </div>
      ) : (
        <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)" }}>
          Photos will be available after the event.
        </p>
      )}
    </div>
  )
}

function LoadingSpinner() {
  return (
    <div style={{ minHeight: "200px", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <p style={{ fontFamily: HN, fontSize: "11px", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(245,243,239,0.3)" }}>
        Loading…
      </p>
    </div>
  )
}

function ErrorBanner({ msg }) {
  return (
    <div style={{ minHeight: "100svh", background: "#080808", display: "flex", alignItems: "center", justifyContent: "center", padding: "40px" }}>
      <p style={{ fontFamily: CH, fontSize: "16px", color: "#D10000", textAlign: "center" }}>{msg}</p>
    </div>
  )
}

export function EventContent({ id, event, settings, error }) {
  const [showInfo, setShowInfo] = useState(Boolean(settings?.payment_blocked))
  const [activeTab, setActiveTab] = useState("info")
  const [eventImageUrl, setEventImageUrl] = useState(null)

  useEffect(() => {
    if (event && analytics) {
      try {
        logEvent(analytics, "page_event_view", {
          event_id: id,
          event_title: event.title ?? "Untitled",
          purchase_mode: resolvePurchaseMode(event),
        })
      } catch {}
    }
  }, [id, event])

  useEffect(() => {
    setShowInfo(Boolean(settings?.payment_blocked))
  }, [settings?.payment_blocked])

  useEffect(() => {
    let mounted = true

    if (!event?.image) {
      setEventImageUrl(null)
      return () => {
        mounted = false
      }
    }

    getImageUrl("events", `${event.image}.jpg`)
      .then((url) => {
        if (mounted) setEventImageUrl(url)
      })
      .catch(() => {
        if (mounted) setEventImageUrl(null)
      })

    return () => {
      mounted = false
    }
  }, [event?.image])

  if (error) return <ErrorBanner msg={error} />
  if (!event || !settings) return <ErrorBanner msg="Evento non disponibile" />

  const Content = EVENT_CONTENT_COMPONENT

  return (
    <div style={{ minHeight: "100svh", background: "#080808" }}>
      <EventHero event={event} imageUrl={eventImageUrl} />

      {/* Tab bar */}
      <div className="event-tabbar" style={{
        borderBottom: "1px solid rgba(245,243,239,0.07)",
        padding: "0 48px",
        display: "flex", gap: 0,
      }}>
        {TABS.map(t => (
          <button key={t} className="event-tab-button" onClick={() => setActiveTab(t)} style={{
            background: "none", border: "none", cursor: "pointer",
            fontFamily: HN, fontSize: "10px",
            fontWeight: activeTab === t ? 700 : 400,
            letterSpacing: "0.28em", textTransform: "uppercase",
            color: activeTab === t ? ACC : "rgba(245,243,239,0.3)",
            padding: "18px 24px 20px",
            borderBottom: activeTab === t ? `2px solid ${ACC}` : "2px solid transparent",
            marginBottom: "-1px", transition: "all 0.2s",
          }}>{t}</button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ maxWidth: "1200px", margin: "0 auto", padding: "56px 48px 80px" }} className="event-detail-content">
        {activeTab === "info" && <InfoTab event={event} />}
        {activeTab === "lineup" && <LineupTab event={event} />}
        {activeTab === "photos" && <PhotosTab event={event} />}
        {activeTab === "join" && <JoinTab />}
      </div>

      {/* Purchase section */}
      <div
        style={{ borderTop: "1px solid rgba(245,243,239,0.06)" }}
      >
        <Suspense fallback={<LoadingSpinner />}>
          <Content id={id} event={event} settings={settings} membershipPrice={settings?.membership_price_per_year ?? null} />
        </Suspense>
      </div>

      <PaymentWarningModal
        open={showInfo}
        onClose={() => setShowInfo(false)}
        price={event.price ?? 18}
        iban={settings.company_iban}
        intestatario={settings.company_intestatario}
      />
    </div>
  )
}
