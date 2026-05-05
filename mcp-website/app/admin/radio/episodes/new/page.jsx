"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { EpisodeForm } from "@/components/admin/radio/EpisodeForm"
import { getSeasons } from "@/services/admin/radio"
import { routes } from "@/config/routes"
import { AdminInlineLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"

export default function NewEpisodePage() {
  const [seasons, setSeasons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function load() {
      const res = await getSeasons()
      if (res?.error) {
        setError(res.error)
      } else {
        setSeasons(res ?? [])
      }
      setLoading(false)
    }
    load()
  }, [])

  return (
    <div>
      <AdminPageHeader title="Nuovo episodio" backHref={routes.admin.radio.index} backLabel="Torna alla radio" />

      {loading && <AdminInlineLoading />}

      {error && (
        <div
          style={{
            padding: "10px 14px",
            background: "#e8241a18",
            border: "1px solid #e8241a44",
            borderRadius: 4,
            color: "#e8241a",
            fontSize: 13,
            fontFamily: "Helvetica Neue, sans-serif",
          }}
        >
          {error}
        </div>
      )}

      {!loading && !error && seasons.length === 0 && (
        <div
          style={{
            padding: "14px 18px",
            background: "#e8820c18",
            border: "1px solid #e8820c44",
            borderRadius: 4,
            color: "#e8820c",
            fontSize: 13,
            fontFamily: "Helvetica Neue, sans-serif",
          }}
        >
          Devi creare almeno una stagione prima di aggiungere un episodio.{" "}
          <Link
            href={routes.admin.radio.newSeason}
            style={{ color: "#e8820c", fontWeight: 700, textDecoration: "underline" }}
          >
            Crea stagione
          </Link>
        </div>
      )}

      {!loading && seasons.length > 0 && <EpisodeForm mode="create" seasons={seasons} />}
    </div>
  )
}
