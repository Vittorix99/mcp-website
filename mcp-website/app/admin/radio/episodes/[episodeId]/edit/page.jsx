"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { EpisodeForm } from "@/components/admin/radio/EpisodeForm"
import { getEpisode, getSeasons } from "@/services/admin/radio"
import { routes } from "@/config/routes"
import { AdminInlineLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"

export default function EditEpisodePage() {
  const params = useParams()
  const episodeId = params?.episodeId
  const [episode, setEpisode] = useState(null)
  const [seasons, setSeasons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!episodeId) return
    async function load() {
      const [epRes, sRes] = await Promise.all([getEpisode(episodeId), getSeasons()])
      if (epRes?.error || sRes?.error) {
        setError(epRes?.error ?? sRes?.error)
      } else {
        setEpisode(epRes)
        setSeasons(sRes ?? [])
      }
      setLoading(false)
    }
    load()
  }, [episodeId])

  return (
    <div>
      <AdminPageHeader title="Modifica episodio" backHref={routes.admin.radio.index} backLabel="Torna alla radio" />

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

      {episode && seasons.length > 0 && (
        <EpisodeForm mode="edit" episode={episode} seasons={seasons} />
      )}
    </div>
  )
}
