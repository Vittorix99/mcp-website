"use client"

import { useState, useEffect, useMemo } from "react"
import Link from "next/link"
import { Plus } from "lucide-react"
import { Table, TableBody, TableHead, TableHeader, TableRow, TableCell } from "@/components/ui/table"
import { SeasonCard } from "@/components/admin/radio/SeasonCard"
import { EpisodeRow } from "@/components/admin/radio/EpisodeRow"
import { getSeasons, getEpisodes } from "@/services/admin/radio"
import { routes } from "@/config/routes"
import { AdminLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"

const headerStyle = {
  fontSize: 10,
  fontWeight: 700,
  textTransform: "uppercase",
  letterSpacing: "0.12em",
  color: "#666666",
  fontFamily: "Helvetica Neue, sans-serif",
  paddingBottom: 8,
}

export default function RadioPage() {
  const [seasons, setSeasons] = useState([])
  const [episodes, setEpisodes] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filterSeason, setFilterSeason] = useState("all")

  useEffect(() => {
    async function load() {
      setLoading(true)
      const [sRes, eRes] = await Promise.all([getSeasons(), getEpisodes()])
      if (sRes?.error || eRes?.error) {
        setError(sRes?.error ?? eRes?.error)
      } else {
        setSeasons(sRes ?? [])
        setEpisodes(eRes ?? [])
      }
      setLoading(false)
    }
    load()
  }, [])

  const filteredEpisodes = useMemo(() => {
    if (filterSeason === "all") return episodes
    return episodes.filter((e) => e.seasonId === filterSeason)
  }, [episodes, filterSeason])

  if (loading) {
    return <AdminLoading label="Caricamento radio..." />
  }

  if (error) {
    return (
      <div
        style={{
          padding: "14px 18px",
          background: "#e8241a18",
          border: "1px solid #e8241a44",
          borderRadius: 6,
          color: "#e8241a",
          fontFamily: "Helvetica Neue, sans-serif",
          fontSize: 14,
        }}
      >
        {error}
      </div>
    )
  }

  return (
    <div style={{ paddingBottom: 64 }}>
      <AdminPageHeader
        title="Radio"
        description="Gestisci stagioni ed episodi del podcast."
      />

      {/* ── Seasons ───────────────────────────────────────────────── */}
      <section style={{ marginBottom: 48 }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 16,
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.12em",
              color: "#b0b0b0",
              fontFamily: "Helvetica Neue, sans-serif",
            }}
          >
            Stagioni
          </h2>
          <Link
            href={routes.admin.radio.newSeason}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "7px 14px",
              background: "#e8820c",
              borderRadius: 4,
              color: "#000000",
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontFamily: "Helvetica Neue, sans-serif",
              textDecoration: "none",
            }}
          >
            <Plus style={{ width: 13, height: 13 }} />
            Nuova stagione
          </Link>
        </div>

        {seasons.length === 0 ? (
          <div
            style={{
              padding: "32px 24px",
              border: "1px dashed #2a2a2a",
              borderRadius: 6,
              textAlign: "center",
              color: "#444444",
              fontSize: 13,
              fontFamily: "Helvetica Neue, sans-serif",
            }}
          >
            Nessuna stagione creata.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {seasons.map((s) => (
              <SeasonCard key={s.id} season={s} />
            ))}
          </div>
        )}
      </section>

      {/* ── Episodes ──────────────────────────────────────────────── */}
      <section>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 16,
            gap: 12,
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <h2
              style={{
                margin: 0,
                fontSize: 11,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.12em",
                color: "#b0b0b0",
                fontFamily: "Helvetica Neue, sans-serif",
              }}
            >
              Episodi
            </h2>
            {seasons.length > 0 && (
              <select
                value={filterSeason}
                onChange={(e) => setFilterSeason(e.target.value)}
                style={{
                  background: "#111111",
                  border: "1px solid #3a3a3a",
                  borderRadius: 4,
                  padding: "5px 10px",
                  color: "#b0b0b0",
                  fontSize: 11,
                  fontFamily: "Helvetica Neue, sans-serif",
                  cursor: "pointer",
                  outline: "none",
                }}
              >
                <option value="all">Tutte le stagioni</option>
                {seasons.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <Link
            href={routes.admin.radio.newEpisode}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              padding: "7px 14px",
              background: "transparent",
              border: "1px solid #e8820c",
              borderRadius: 4,
              color: "#e8820c",
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontFamily: "Helvetica Neue, sans-serif",
              textDecoration: "none",
            }}
          >
            <Plus style={{ width: 13, height: 13 }} />
            Nuovo episodio
          </Link>
        </div>

        {filteredEpisodes.length === 0 ? (
          <div
            style={{
              padding: "32px 24px",
              border: "1px dashed #2a2a2a",
              borderRadius: 6,
              textAlign: "center",
              color: "#444444",
              fontSize: 13,
              fontFamily: "Helvetica Neue, sans-serif",
            }}
          >
            Nessun episodio creato.
          </div>
        ) : (
          <div
            style={{
              background: "#0a0a0a",
              border: "1px solid #1e1e1e",
              borderRadius: 6,
              overflow: "hidden",
            }}
          >
            <Table>
              <TableHeader>
                <TableRow style={{ borderColor: "#1e1e1e" }}>
                  <TableHead style={{ ...headerStyle, width: 56 }} />
                  <TableHead style={{ ...headerStyle, width: 64 }}>Ep.</TableHead>
                  <TableHead style={headerStyle}>Titolo</TableHead>
                  <TableHead style={headerStyle}>Stagione</TableHead>
                  <TableHead style={headerStyle}>Durata</TableHead>
                  <TableHead style={headerStyle}>Generi</TableHead>
                  <TableHead style={headerStyle}>Stato</TableHead>
                  <TableHead style={headerStyle}>Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredEpisodes.map((ep) => (
                  <EpisodeRow key={ep.id} episode={ep} seasons={seasons} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>
    </div>
  )
}
