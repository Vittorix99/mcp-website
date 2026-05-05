"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { getImageUrl } from "@/config/firebaseStorage"
import { routes, getRoute } from "@/config/routes"
import { SectionLabel } from "@/components/SectionLabel"
import { useReveal } from "@/hooks/useReveal"

const ACC = "#E07800"
const RED = "#D10000"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

export function NextEventSection({ event }) {
  useReveal()
  const [imageUrl, setImageUrl] = useState(null)

  useEffect(() => {
    if (!event?.image) return
    getImageUrl("events", `${event.image}.jpg`).then(setImageUrl).catch(() => {})
  }, [event])

  if (!event) return null

  let formattedDate = event.date || ""
  try {
    const [day, month, year] = (event.date || "").split("-").map(Number)
    formattedDate = `${day.toString().padStart(2, "0")}.${month.toString().padStart(2, "0")}.${year}`
  } catch {}

  const filteredLineup = (event.lineup || []).filter(a => a.trim() !== "")
  const publicLocation = event.locationHint || event.location || ""
  const timeStr = event.startTime && event.endTime ? `${event.startTime} — ${event.endTime}` : ""
  const eventHref = getRoute(routes.events.details, event.slug)

  return (
    <section style={{ padding: "120px 0 100px", background: "#080808" }}>
      <div style={{ maxWidth: "1360px", margin: "0 auto", padding: "0 40px" }}>
        <SectionLabel text="Next Event" />

        <div className="next-event-grid-new reveal">
          {/* Flyer */}
          <div style={{
            position: "relative", aspectRatio: "3/4", maxHeight: "580px",
            overflow: "hidden", background: "#0f0f0f",
            border: "1px solid rgba(245,243,239,0.05)",
          }}>
            {imageUrl ? (
              <Image
                src={imageUrl}
                alt={event.title}
                fill
                style={{ objectFit: "cover" }}
              />
            ) : (
              <>
                <div style={{
                  position: "absolute", inset: 0,
                  backgroundImage: `repeating-linear-gradient(-45deg,
                    rgba(224,120,0,0.035) 0px, rgba(224,120,0,0.035) 1px,
                    transparent 1px, transparent 14px)`,
                }} />
                <div style={{
                  position: "absolute", inset: 0,
                  display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center", gap: "6px",
                }}>
                  <p style={{ fontFamily: HN, fontSize: "8px", letterSpacing: "0.3em", textTransform: "uppercase", color: "rgba(245,243,239,0.18)", margin: 0 }}>Event flyer</p>
                  <p style={{ fontFamily: CH, fontSize: "11px", fontStyle: "italic", color: "rgba(245,243,239,0.1)", margin: 0 }}>Loading…</p>
                </div>
              </>
            )}
            <div style={{ position: "absolute", top: 0, left: 0, width: "3px", height: "72px", background: ACC }} />
            <div style={{ position: "absolute", bottom: 0, right: 0, width: "72px", height: "3px", background: RED }} />
          </div>

          {/* Info */}
          <div className="next-event-info" style={{ padding: "0 0 0 72px" }}>
            <p style={{ fontFamily: CH, fontSize: "13px", fontStyle: "italic", color: "rgba(245,243,239,0.35)", marginBottom: "20px", margin: "0 0 20px" }}>
              {formattedDate}
            </p>
            <h2 style={{
              fontFamily: HN, fontWeight: 900,
              fontSize: "clamp(36px,4.5vw,68px)", letterSpacing: "-0.03em",
              textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.88,
              marginBottom: "36px",
            }}>{event.title}</h2>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "40px" }}>
              {[
                ["Location", publicLocation],
                ["Time", timeStr],
              ].filter(([, v]) => v).map(([k, v]) => (
                <div key={k} style={{ display: "flex", gap: "28px", alignItems: "baseline" }}>
                  <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.35em", textTransform: "uppercase", color: ACC, minWidth: "72px", margin: 0 }}>{k}</p>
                  <p style={{ fontFamily: HN, fontSize: "14px", color: "rgba(245,243,239,0.7)", letterSpacing: "0.04em", margin: 0 }}>{v}</p>
                </div>
              ))}
            </div>

            {filteredLineup.length > 0 && (
              <div style={{ marginBottom: "44px" }}>
                <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.35em", textTransform: "uppercase", color: ACC, marginBottom: "14px" }}>Lineup</p>
                {filteredLineup.map((a, i) => (
                  <p key={i} style={{
                    fontFamily: HN,
                    fontWeight: i === 0 ? 700 : 300,
                    fontSize: i === 0 ? "22px" : "17px",
                    letterSpacing: i === 0 ? "0.04em" : "0.08em",
                    textTransform: "uppercase",
                    color: i === 0 ? "#F5F3EF" : "rgba(245,243,239,0.5)",
                    borderBottom: i < filteredLineup.length - 1 ? "1px solid rgba(245,243,239,0.05)" : "none",
                    paddingBottom: "8px", margin: 0,
                  }}>{a}</p>
                ))}
              </div>
            )}

            {event.status === "active" ? (
              <Link
                href={eventHref}
                style={{
                  display: "inline-block", padding: "14px 48px", background: ACC,
                  borderRadius: "2px", fontFamily: HN, fontWeight: 700,
                  fontSize: "10px", letterSpacing: "0.3em", textTransform: "uppercase",
                  color: "#fff", textDecoration: "none",
                }}
              >Tickets &amp; Info →</Link>
            ) : (
              <Link
                href={eventHref}
                style={{
                  display: "inline-block", padding: "14px 48px",
                  border: "1px solid rgba(245,243,239,0.18)", borderRadius: "2px",
                  fontFamily: HN, fontWeight: 400,
                  fontSize: "10px", letterSpacing: "0.3em", textTransform: "uppercase",
                  color: "rgba(245,243,239,0.45)", textDecoration: "none",
                }}
              >More Info →</Link>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
