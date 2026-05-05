"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import { SeasonForm } from "@/components/admin/radio/SeasonForm"
import { getSeason } from "@/services/admin/radio"
import { routes } from "@/config/routes"
import { AdminInlineLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"

export default function EditSeasonPage() {
  const params = useParams()
  const seasonId = params?.seasonId
  const [season, setSeason] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!seasonId) return
    async function load() {
      const res = await getSeason(seasonId)
      if (res?.error) {
        setError(res.error)
      } else {
        setSeason(res)
      }
      setLoading(false)
    }
    load()
  }, [seasonId])

  return (
    <div>
      <AdminPageHeader title="Modifica stagione" backHref={routes.admin.radio.index} backLabel="Torna alla radio" />

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

      {season && <SeasonForm mode="edit" season={season} />}
    </div>
  )
}
