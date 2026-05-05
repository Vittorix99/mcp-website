"use client"

import { useState, useMemo, useEffect } from "react"
import Link from "next/link"
import { RadioCard } from "@/components/pages/RadioCard"
import { useReveal } from "@/hooks/useReveal"
import { getPublishedEpisodes, getRadioSeasons } from "@/services/radio"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

export default function RadioClient({ initialEpisodes = [], initialSeasons = [] }) {
  useReveal()
  const [episodes, setEpisodes] = useState(initialEpisodes)
  const [seasons, setSeasons] = useState(initialSeasons)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (initialEpisodes.length > 0) return
    let cancelled = false
    setLoading(true)
    ;(async () => {
      try {
        const [epRes, seRes] = await Promise.all([getPublishedEpisodes(), getRadioSeasons()])
        if (cancelled) return
        if (epRes.success) setEpisodes(epRes.episodes)
        if (seRes.success) setSeasons(seRes.seasons)
        setError(null)
      } catch {
        if (!cancelled) setError("Unable to load episodes.")
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [initialEpisodes.length])

  // Group episodes by season, sorted by episodeNumber desc
  const seasonedGroups = useMemo(() => {
    const sorted = [...episodes].sort((a, b) => (b.episodeNumber || 0) - (a.episodeNumber || 0))
    if (seasons.length === 0) return [{ season: null, episodes: sorted }]

    const seasonMap = new Map(seasons.map(s => [s.id, s]))
    const groups = new Map()

    for (const ep of sorted) {
      const sid = ep.seasonId || "__none__"
      if (!groups.has(sid)) groups.set(sid, [])
      groups.get(sid).push(ep)
    }

    // Sort season groups by year desc, then by name
    const result = []
    for (const [sid, eps] of groups) {
      const season = seasonMap.get(sid) || null
      result.push({ season, episodes: eps })
    }
    result.sort((a, b) => {
      const ya = a.season?.year || 0
      const yb = b.season?.year || 0
      return yb - ya
    })
    return result
  }, [episodes, seasons])

  const totalEpisodes = episodes.length

  return (
    <div style={{ minHeight: "100svh", background: "#080808", paddingTop: "100px" }}>

      {/* Page header */}
      <div style={{ padding: "40px 40px 0" }}>
        <Link href="/" style={{
          fontFamily: HN, fontSize: "9px", letterSpacing: "0.32em",
          textTransform: "uppercase", color: "rgba(245,243,239,0.35)",
          textDecoration: "none", display: "block", marginBottom: "28px",
        }}>← Home</Link>

        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: "16px", marginBottom: "16px" }}>
          <h1 style={{
            fontFamily: HN, fontWeight: 900,
            fontSize: "clamp(48px,10vw,120px)", letterSpacing: "-0.04em",
            textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.84,
            margin: 0,
          }}>MCP Radio</h1>
          <a
            href="https://soundcloud.com/music_connectingpeople"
            target="_blank"
            rel="noreferrer"
            style={{
              fontFamily: HN, fontSize: "10px", fontWeight: 700,
              letterSpacing: "0.26em", textTransform: "uppercase",
              color: "rgba(245,243,239,0.4)", textDecoration: "none",
              borderBottom: "1px solid rgba(245,243,239,0.14)", paddingBottom: "2px",
              marginBottom: "12px",
            }}
          >SoundCloud ↗</a>
        </div>
        <p style={{
          fontFamily: CH, fontSize: "16px", fontStyle: "italic",
          color: "rgba(245,243,239,0.35)", marginBottom: "64px",
        }}>
          {totalEpisodes > 0 ? `${totalEpisodes} episode${totalEpisodes !== 1 ? "s" : ""} · available on SoundCloud` : "Available on SoundCloud"}
        </p>
      </div>

      {/* Loading / error */}
      {loading && (
        <p style={{ fontFamily: HN, fontSize: "10px", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(245,243,239,0.3)", padding: "0 40px" }}>
          Loading…
        </p>
      )}
      {error && (
        <p style={{ fontFamily: CH, fontSize: "14px", color: "#D10000", padding: "0 40px" }}>{error}</p>
      )}
      {!loading && !error && totalEpisodes === 0 && (
        <p style={{ fontFamily: CH, fontSize: "16px", fontStyle: "italic", color: "rgba(245,243,239,0.35)", padding: "0 40px" }}>
          No episodes available yet.
        </p>
      )}

      {/* Seasons + episode grids */}
      {seasonedGroups.map(({ season, episodes: eps }, gi) => (
        <div key={season?.id || gi} style={{ marginBottom: "80px" }}>

          {/* Season header */}
          {season && (
            <div style={{
              padding: "0 40px", marginBottom: "32px",
              display: "flex", alignItems: "baseline", gap: "24px",
            }}>
              <div style={{ width: "3px", height: "36px", background: ACC, flexShrink: 0, alignSelf: "center" }} />
              <div>
                <p style={{
                  fontFamily: HN, fontSize: "8px", fontWeight: 700,
                  letterSpacing: "0.4em", textTransform: "uppercase",
                  color: ACC, margin: "0 0 4px",
                }}>Season · {season.year}</p>
                <h2 style={{
                  fontFamily: HN, fontWeight: 900,
                  fontSize: "clamp(22px,3vw,38px)", letterSpacing: "-0.025em",
                  textTransform: "uppercase", color: "#F5F3EF", margin: 0,
                  lineHeight: 1,
                }}>{season.name}</h2>
                {season.description && (
                  <p style={{
                    fontFamily: CH, fontSize: "14px", fontStyle: "italic",
                    color: "rgba(245,243,239,0.45)", margin: "8px 0 0", maxWidth: "480px",
                  }}>{season.description}</p>
                )}
              </div>
              <span style={{
                fontFamily: HN, fontSize: "10px", letterSpacing: "0.2em",
                textTransform: "uppercase", color: "rgba(245,243,239,0.18)",
                marginLeft: "auto",
              }}>{eps.length} ep.</span>
            </div>
          )}

          {/* Episodes grid */}
          <div className="radio-grid">
            {eps.map((ep, i) => (
              <RadioCard key={ep.id || i} episode={ep} index={i} />
            ))}
          </div>

          {/* Season separator */}
          {gi < seasonedGroups.length - 1 && (
            <div style={{
              margin: "64px 40px 0",
              height: "1px",
              background: "linear-gradient(to right, rgba(224,120,0,0.25), transparent)",
            }} />
          )}
        </div>
      ))}

      {/* Footer link */}
      <div style={{ padding: "0 40px 80px", textAlign: "center" }}>
        <a
          href="https://soundcloud.com/music_connectingpeople"
          target="_blank"
          rel="noreferrer"
          style={{
            fontFamily: HN, fontSize: "10px", fontWeight: 700,
            letterSpacing: "0.26em", textTransform: "uppercase",
            color: "rgba(245,243,239,0.4)", textDecoration: "none",
            borderBottom: "1px solid rgba(245,243,239,0.14)", paddingBottom: "2px",
          }}
        >Explore on SoundCloud ↗</a>
      </div>
    </div>
  )
}
