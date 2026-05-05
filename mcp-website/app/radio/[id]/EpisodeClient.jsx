"use client"

import { useState, useRef, useEffect } from "react"
import Link from "next/link"
import { useReveal } from "@/hooks/useReveal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

function formatDuration(ms) {
  if (!ms) return null
  const total = Math.floor(ms / 1000)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
  return `${m}:${String(s).padStart(2, "0")}`
}

function getYouTubeId(url) {
  if (!url) return null
  const m = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|shorts\/))([a-zA-Z0-9_-]{11})/)
  return m ? m[1] : null
}

function MetaRow({ label, value }) {
  if (!value) return null
  return (
    <div style={{ display: "flex", gap: "16px", alignItems: "baseline", borderBottom: "1px solid rgba(245,243,239,0.06)", padding: "14px 0" }}>
      <span style={{
        fontFamily: HN, fontSize: "8px", fontWeight: 700,
        letterSpacing: "0.38em", textTransform: "uppercase",
        color: ACC, minWidth: "80px", flexShrink: 0,
      }}>{label}</span>
      <span style={{ fontFamily: CH, fontSize: "15px", color: "rgba(245,243,239,0.72)", lineHeight: 1.5 }}>{value}</span>
    </div>
  )
}

function EpisodeNav({ label, episode, align = "left" }) {
  if (!episode) return <div />
  return (
    <Link
      href={`/radio/${episode.id}`}
      style={{
        display: "flex", flexDirection: "column",
        gap: "6px", textDecoration: "none",
        alignItems: align === "right" ? "flex-end" : "flex-start",
        padding: "16px 20px",
        background: "rgba(245,243,239,0.03)",
        border: "1px solid rgba(245,243,239,0.07)",
        borderRadius: "2px",
        transition: "background 0.2s",
        flex: 1,
      }}
      onMouseEnter={e => e.currentTarget.style.background = "rgba(245,243,239,0.06)"}
      onMouseLeave={e => e.currentTarget.style.background = "rgba(245,243,239,0.03)"}
    >
      <span style={{ fontFamily: HN, fontSize: "8px", letterSpacing: "0.3em", textTransform: "uppercase", color: "rgba(245,243,239,0.3)" }}>{label}</span>
      <span style={{ fontFamily: HN, fontSize: "13px", fontWeight: 700, letterSpacing: "0.02em", textTransform: "uppercase", color: "#F5F3EF", lineHeight: 1.2 }}>
        {episode.title}
      </span>
      <span style={{ fontFamily: HN, fontSize: "8px", letterSpacing: "0.2em", color: ACC }}>Ep. {episode.episodeNumber}</span>
    </Link>
  )
}

export default function EpisodeClient({ episode, prevEpisode, nextEpisode }) {
  useReveal()
  const [showPlayer, setShowPlayer] = useState(false)

  if (!episode) {
    return (
      <div style={{ minHeight: "100svh", background: "#080808", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: "24px" }}>
        <p style={{ fontFamily: HN, fontSize: "11px", letterSpacing: "0.3em", textTransform: "uppercase", color: "rgba(245,243,239,0.3)" }}>Episode not found</p>
        <Link href="/radio" style={{ fontFamily: HN, fontSize: "9px", letterSpacing: "0.3em", textTransform: "uppercase", color: ACC, textDecoration: "none" }}>← Back to Radio</Link>
      </div>
    )
  }

  const artworkUrl = episode.soundcloudArtworkUrl
  const scUrl = episode.soundcloudUrl
  const videoUrls = episode.videoUrls || []
  const genres = episode.genres || []
  const duration = formatDuration(episode.duration)

  const recordedDate = episode.recordedAt
    ? new Date(episode.recordedAt).toLocaleDateString("it-IT", { year: "numeric", month: "long", day: "numeric" })
    : null
  const publishedDate = episode.publishedAt
    ? new Date(episode.publishedAt).toLocaleDateString("it-IT", { year: "numeric", month: "long" })
    : null

  return (
    <div style={{ minHeight: "100svh", background: "#080808" }}>

      {/* Hero */}
      <div style={{ position: "relative", height: "70svh", minHeight: "480px", overflow: "hidden" }}>

        {/* Artwork bg */}
        {artworkUrl ? (
          <img
            src={artworkUrl}
            alt=""
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", filter: "brightness(0.3) saturate(0.6)" }}
          />
        ) : (
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(135deg, #150820 0%, #0a0a0a 60%, #100508 100%)" }} />
        )}

        {/* Gradient overlay */}
        <div style={{ position: "absolute", inset: 0, background: "linear-gradient(to bottom, rgba(8,8,8,0.2) 0%, rgba(8,8,8,0.5) 60%, #080808 100%)" }} />

        {/* Top accent bar */}
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "3px", background: `linear-gradient(to right, ${ACC}, transparent 60%)` }} />

        {/* Navigation bar */}
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0,
          display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "80px 40px 0",
        }}>
          <Link href="/radio" style={{
            fontFamily: HN, fontSize: "9px", letterSpacing: "0.32em",
            textTransform: "uppercase", color: "rgba(245,243,239,0.4)",
            textDecoration: "none",
          }}>← MCP Radio</Link>
          <span style={{ fontFamily: HN, fontSize: "8px", letterSpacing: "0.3em", textTransform: "uppercase", color: "rgba(245,243,239,0.2)" }}>
            Ep. {episode.episodeNumber}
          </span>
        </div>

        {/* Hero content */}
        <div style={{
          position: "absolute", bottom: 0, left: 0, right: 0,
          padding: "0 40px 48px",
          display: "flex", alignItems: "flex-end", justifyContent: "space-between",
          gap: "24px", flexWrap: "wrap",
        }}>
          <div style={{ flex: 1, minWidth: "200px" }}>
            {genres.length > 0 && (
              <div style={{ display: "flex", gap: "8px", marginBottom: "16px", flexWrap: "wrap" }}>
                {genres.map(g => (
                  <span key={g} style={{
                    fontFamily: HN, fontSize: "7px", fontWeight: 700,
                    letterSpacing: "0.3em", textTransform: "uppercase",
                    color: ACC, border: `1px solid rgba(224,120,0,0.35)`,
                    padding: "4px 10px",
                  }}>{g}</span>
                ))}
              </div>
            )}
            <h1 style={{
              fontFamily: HN, fontWeight: 900,
              fontSize: "clamp(28px,5vw,72px)", letterSpacing: "-0.03em",
              textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.9,
              margin: "0 0 12px",
            }}>{episode.title}</h1>
            {duration && (
              <p style={{ fontFamily: CH, fontSize: "14px", fontStyle: "italic", color: "rgba(245,243,239,0.4)", margin: 0 }}>
                {duration}
              </p>
            )}
          </div>

          {/* Play button */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px", alignItems: "flex-end" }}>
            {!showPlayer ? (
              <button
                onClick={() => setShowPlayer(true)}
                style={{
                  display: "flex", alignItems: "center", gap: "14px",
                  padding: "14px 28px",
                  background: ACC, border: "none", borderRadius: "2px",
                  cursor: "pointer", fontFamily: HN, fontSize: "10px",
                  fontWeight: 700, letterSpacing: "0.26em", textTransform: "uppercase",
                  color: "#fff",
                }}
              >
                <span style={{ display: "flex", width: 0, height: 0, borderTop: "7px solid transparent", borderBottom: "7px solid transparent", borderLeft: "11px solid #fff" }} />
                Play Episode
              </button>
            ) : (
              <button
                onClick={() => setShowPlayer(false)}
                style={{
                  padding: "14px 28px",
                  background: "rgba(0,0,0,0.5)", border: "1px solid rgba(245,243,239,0.2)",
                  borderRadius: "2px", cursor: "pointer",
                  fontFamily: HN, fontSize: "10px", fontWeight: 700,
                  letterSpacing: "0.26em", textTransform: "uppercase",
                  color: "rgba(245,243,239,0.6)",
                }}
              >✕ Close Player</button>
            )}
            <a
              href={scUrl}
              target="_blank"
              rel="noreferrer"
              style={{
                fontFamily: HN, fontSize: "8px", letterSpacing: "0.22em",
                textTransform: "uppercase", color: "rgba(245,243,239,0.35)",
                textDecoration: "none",
                borderBottom: "1px solid rgba(245,243,239,0.15)", paddingBottom: "2px",
              }}
            >Open on SoundCloud ↗</a>
          </div>
        </div>
      </div>

      {/* SoundCloud Player */}
      {showPlayer && (
        <div style={{ background: "#0a0a0a", borderBottom: "1px solid rgba(245,243,239,0.06)" }}>
          <iframe
            width="100%"
            height="166"
            scrolling="no"
            frameBorder="no"
            allow="autoplay"
            src={`https://w.soundcloud.com/player/?url=${encodeURIComponent(scUrl)}&color=%23E07800&auto_play=true&hide_related=true&show_comments=false&show_user=true&show_reposts=false&show_teaser=false`}
            style={{ display: "block" }}
          />
        </div>
      )}

      {/* Body */}
      <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "64px 40px" }}>
        <div className="episode-detail-grid" style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: "80px", alignItems: "start" }}>

          {/* Left: description + videos */}
          <div>
            {episode.description && (
              <div className="reveal" style={{ marginBottom: "56px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "24px" }}>
                  <div style={{ width: "36px", height: "1px", background: ACC }} />
                  <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.4em", textTransform: "uppercase", color: ACC, margin: 0 }}>About</p>
                </div>
                <p style={{ fontFamily: CH, fontSize: "17px", lineHeight: 1.85, color: "rgba(245,243,239,0.65)", margin: 0 }}>
                  {episode.description}
                </p>
              </div>
            )}

            {/* Video section */}
            {videoUrls.length > 0 && (
              <div className="reveal">
                <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "28px" }}>
                  <div style={{ width: "36px", height: "1px", background: ACC }} />
                  <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.4em", textTransform: "uppercase", color: ACC, margin: 0 }}>Video</p>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
                  {videoUrls.map((url, i) => {
                    const ytId = getYouTubeId(url)
                    return (
                      <div key={i} style={{ position: "relative", paddingBottom: "56.25%", height: 0, overflow: "hidden", background: "#0a0a0a" }}>
                        {ytId ? (
                          <iframe
                            src={`https://www.youtube.com/embed/${ytId}?rel=0&color=white`}
                            title={`Video ${i + 1}`}
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                            style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%", border: "none" }}
                          />
                        ) : (
                          <video
                            src={url}
                            controls
                            preload="metadata"
                            poster={artworkUrl || undefined}
                            style={{
                              position: "absolute", inset: 0,
                              width: "100%", height: "100%",
                              objectFit: "contain",
                              background: "#050505",
                            }}
                          >
                            <a href={url} target="_blank" rel="noreferrer">Watch Video</a>
                          </video>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Right: metadata panel */}
          <div className="reveal reveal-delay-2">
            <div style={{
              background: "rgba(245,243,239,0.03)",
              border: "1px solid rgba(245,243,239,0.07)",
              borderTop: `2px solid ${ACC}`,
              padding: "28px",
            }}>
              {artworkUrl && (
                <img
                  src={artworkUrl}
                  alt={episode.title}
                  style={{ width: "100%", aspectRatio: "1/1", objectFit: "cover", display: "block", marginBottom: "24px" }}
                />
              )}
              <MetaRow label="Episode" value={`#${episode.episodeNumber}`} />
              <MetaRow label="Duration" value={duration} />
              <MetaRow label="Recorded" value={recordedDate} />
              <MetaRow label="Published" value={publishedDate} />
              {genres.length > 0 && (
                <MetaRow label="Genre" value={genres.join(" · ")} />
              )}
            </div>
          </div>
        </div>

        {/* Prev / Next navigation */}
        {(prevEpisode || nextEpisode) && (
          <div className="reveal" style={{ marginTop: "80px", paddingTop: "40px", borderTop: "1px solid rgba(245,243,239,0.06)" }}>
            <p style={{ fontFamily: HN, fontSize: "8px", fontWeight: 700, letterSpacing: "0.38em", textTransform: "uppercase", color: "rgba(245,243,239,0.2)", marginBottom: "20px" }}>More episodes</p>
            <div style={{ display: "flex", gap: "12px" }}>
              <EpisodeNav label="← Previous" episode={prevEpisode} align="left" />
              <EpisodeNav label="Next →" episode={nextEpisode} align="right" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
