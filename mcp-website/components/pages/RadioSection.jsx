"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { RadioCard } from "@/components/pages/RadioCard"
import { useReveal } from "@/hooks/useReveal"
import { getPublishedEpisodes } from "@/services/radio"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"

export function RadioSection({ episodes: initialEpisodes = [] }) {
  const [episodes, setEpisodes] = useState(initialEpisodes)
  useReveal()

  useEffect(() => {
    if (initialEpisodes.length > 0) return
    getPublishedEpisodes().then(res => {
      if (res.success && res.episodes.length > 0) setEpisodes(res.episodes)
    }).catch(() => {})
  }, [initialEpisodes.length])

  const displayEpisodes = [...episodes]
    .sort((a, b) => (b.episodeNumber || 0) - (a.episodeNumber || 0))
    .slice(0, 6)

  return (
    <section className="radio-section" style={{
      background: "#080808", paddingTop: "120px",
      borderTop: "1px solid rgba(245,243,239,0.04)",
    }}>
      <div className="radio-section-header" style={{
        padding: "0 40px", marginBottom: "52px",
        display: "flex", alignItems: "center",
        justifyContent: "space-between", flexWrap: "wrap", gap: "16px",
      }}>
        <div className="radio-section-kicker" style={{ display: "flex", alignItems: "center", gap: "20px" }}>
          <div style={{ width: "36px", height: "1px", background: ACC }} />
          <p style={{
            fontFamily: HN, fontSize: "9px", fontWeight: 700,
            letterSpacing: "0.4em", textTransform: "uppercase",
            color: ACC, margin: 0,
          }}>MCP Radio</p>
        </div>
        <h2 className="radio-section-title" style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(28px,5vw,72px)", letterSpacing: "-0.03em",
          textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.9, margin: 0,
        }}>Listen</h2>
        <a
          className="radio-section-link"
          href="https://soundcloud.com/music_connectingpeople"
          target="_blank" rel="noreferrer"
          style={{
            fontFamily: HN, fontSize: "10px", letterSpacing: "0.2em",
            textTransform: "uppercase", color: "rgba(245,243,239,0.38)",
            textDecoration: "none",
            borderBottom: "1px solid rgba(245,243,239,0.14)", paddingBottom: "2px",
          }}
        >All on SoundCloud ↗</a>
      </div>

      <div className={`radio-grid ${displayEpisodes.length === 1 ? "radio-grid--single" : ""}`}>
        {displayEpisodes.length > 0
          ? displayEpisodes.map((ep, i) => (
              <RadioCard key={ep.id || i} episode={ep} index={i} />
            ))
          : Array.from({ length: 4 }).map((_, i) => (
              <div key={i} style={{
                background: ["#200040","#001530","#200008","#0a0a0a"][i],
                aspectRatio: "1/1",
                display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                <p style={{
                  fontFamily: HN, fontSize: "8px", letterSpacing: "0.2em",
                  textTransform: "uppercase", color: "rgba(245,243,239,0.15)",
                }}>MCP Radio</p>
              </div>
            ))
        }
      </div>

      {episodes.length > 6 && (
        <div style={{ textAlign: "center", padding: "0 0 40px" }}>
          <Link
            href="/radio"
            style={{
              display: "inline-block",
              padding: "12px 32px",
              border: "1px solid rgba(245,243,239,0.18)", borderRadius: "2px",
              fontFamily: HN, fontSize: "10px", letterSpacing: "0.26em",
              textTransform: "uppercase", color: "rgba(245,243,239,0.55)",
              textDecoration: "none",
            }}
          >View All Episodes →</Link>
        </div>
      )}
    </section>
  )
}
