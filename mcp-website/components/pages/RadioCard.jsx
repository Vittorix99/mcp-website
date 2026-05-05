"use client"

import { useState } from "react"
import Link from "next/link"
import { getEpisodeSlug } from "@/lib/utils/radio"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const FALLBACK_BGS = [
  "#200040", "#001530", "#200008", "#0a0a0a", "#041510", "#120018",
]

export function RadioCard({ episode, index = 0 }) {
  const [hov, setHov] = useState(false)
  const [showEmbed, setShowEmbed] = useState(false)

  const bg = FALLBACK_BGS[index % FALLBACK_BGS.length]
  const scUrl = episode.soundcloudUrl
  const artworkUrl = episode.customArtworkUrl || episode.soundcloudArtworkUrl

  return (
    <div
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      className="reveal"
      style={{
        background: bg, position: "relative",
        aspectRatio: "1/1", overflow: "hidden",
        cursor: "pointer", transition: "transform 0.3s ease",
        transform: hov ? "scale(1.025)" : "scale(1)",
      }}
    >
      {/* Artwork background */}
      {artworkUrl && (
        <img
          src={artworkUrl}
          alt=""
          style={{
            position: "absolute", inset: 0,
            width: "100%", height: "100%",
            objectFit: "cover", opacity: 0.4,
            pointerEvents: "none",
          }}
        />
      )}

      {/* Diagonal texture */}
      <div style={{
        position: "absolute", inset: 0, pointerEvents: "none",
        backgroundImage: `repeating-linear-gradient(-30deg,
          rgba(255,255,255,0.018) 0px,rgba(255,255,255,0.018) 1px,
          transparent 1px,transparent 12px)`,
      }} />

      {/* Darkening overlay */}
      <div style={{
        position: "absolute", inset: 0,
        background: hov ? "rgba(0,0,0,0.55)" : "rgba(0,0,0,0.35)",
        transition: "background 0.25s",
        pointerEvents: "none",
      }} />

      {/* SoundCloud embed */}
      {showEmbed && (
        <div style={{
          position: "absolute", inset: 0, zIndex: 10,
          background: "rgba(0,0,0,0.95)",
          display: "flex", flexDirection: "column",
        }}>
          <button
            onClick={e => { e.stopPropagation(); setShowEmbed(false) }}
            style={{
              alignSelf: "flex-end", background: "none", border: "none",
              cursor: "pointer", color: "rgba(245,243,239,0.5)",
              fontSize: "18px", padding: "12px 14px",
            }}
          >✕</button>
          <iframe
            width="100%"
            height="calc(100% - 44px)"
            scrolling="no"
            frameBorder="no"
            allow="autoplay"
            src={`https://w.soundcloud.com/player/?url=${encodeURIComponent(scUrl)}&color=%23E07800&auto_play=true&hide_related=true&show_comments=false&show_user=true&show_reposts=false&show_teaser=false&visual=true`}
            style={{ border: "none" }}
          />
        </div>
      )}

      {/* Hover: play + detail link */}
      <div style={{
        position: "absolute", inset: 0,
        zIndex: 4,
        opacity: hov ? 1 : 0, transition: "opacity 0.25s",
        display: "flex", alignItems: "center", justifyContent: "center",
        flexDirection: "column", gap: "12px",
      }}>
        <button
          onClick={(e) => { e.stopPropagation(); setShowEmbed(true) }}
          style={{
            width: "52px", height: "52px",
            border: `2px solid ${ACC}`, borderRadius: "50%",
            background: "transparent", cursor: "pointer",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}
        >
          <div style={{
            width: 0, height: 0,
            borderTop: "9px solid transparent",
            borderBottom: "9px solid transparent",
            borderLeft: `14px solid ${ACC}`,
            marginLeft: "4px",
          }} />
        </button>
        {episode.id && (
          <Link
            href={`/radio/${getEpisodeSlug(episode)}`}
            onClick={e => e.stopPropagation()}
            style={{
              fontFamily: HN, fontSize: "8px", letterSpacing: "0.2em",
              textTransform: "uppercase", color: "rgba(245,243,239,0.5)",
              textDecoration: "none",
              borderBottom: "1px solid rgba(245,243,239,0.2)", paddingBottom: "1px",
            }}
          >Episode Details →</Link>
        )}
      </div>

      {/* Bottom text */}
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0, padding: "20px 14px 14px",
        background: "linear-gradient(to top, rgba(0,0,0,0.88), transparent)",
        zIndex: 2,
        pointerEvents: "none",
      }}>
        <p style={{
          fontFamily: HN, fontSize: "7px", fontWeight: 700,
          letterSpacing: "0.28em", textTransform: "uppercase",
          color: ACC, marginBottom: "4px", margin: "0 0 4px",
        }}>MCP Radio</p>
        <p style={{
          fontFamily: HN, fontWeight: 700, fontSize: "14px",
          letterSpacing: "0.02em", textTransform: "uppercase",
          color: "#F5F3EF", margin: "0 0 2px",
          display: "-webkit-box",
          WebkitBoxOrient: "vertical",
          WebkitLineClamp: 2,
          overflow: "hidden",
        }}>{episode.title}</p>
        {episode.description && (
          <p style={{
            fontFamily: CH, fontSize: "12px", fontStyle: "italic",
            color: "rgba(245,243,239,0.55)", margin: 0,
            display: "-webkit-box",
            WebkitBoxOrient: "vertical",
            WebkitLineClamp: 3,
            overflow: "hidden",
          }}>{episode.description}</p>
        )}
      </div>

      {/* Left accent bar */}
      <div style={{
        position: "absolute", top: 0, left: 0,
        width: "3px", height: "36px",
        background: ACC, opacity: hov ? 1 : 0.35,
        transition: "opacity 0.25s",
      }} />
    </div>
  )
}
