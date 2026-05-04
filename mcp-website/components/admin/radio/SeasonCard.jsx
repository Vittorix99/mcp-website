"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Pencil, Trash2, Loader2 } from "lucide-react"
import { routes } from "@/config/routes"
import { deleteSeason } from "@/services/admin/radio"

/**
 * @param {{ season: import('@/types/radio').RadioSeason }} props
 */
export function SeasonCard({ season }) {
  const router = useRouter()
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    if (!confirm(`Eliminare la stagione "${season.name}"?`)) return
    setDeleting(true)
    const res = await deleteSeason(season.id)
    if (res?.error) {
      window.dispatchEvent(new CustomEvent("errorToast", { detail: res.error }))
    } else {
      router.refresh()
    }
    setDeleting(false)
  }

  return (
    <div
      className="group flex items-center justify-between gap-4 rounded px-5 py-4 transition-all duration-150"
      style={{
        background: "#111111",
        border: "1px solid #1e1e1e",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#e8820c")}
      onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#1e1e1e")}
    >
      {/* Left: name + year */}
      <div className="flex flex-col gap-1">
        <span
          className="text-sm font-black uppercase tracking-widest"
          style={{ color: "#ffffff", fontFamily: "Helvetica Neue, sans-serif" }}
        >
          {season.name}
        </span>
        <span
          className="text-xs font-bold uppercase tracking-widest"
          style={{ color: "#e8820c", fontFamily: "Helvetica Neue, sans-serif" }}
        >
          {season.year}
        </span>
      </div>

      {/* Right: actions */}
      <div className="flex items-center gap-2">
        <Link
          href={routes.admin.radio.editSeason(season.id)}
          className="flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-bold uppercase tracking-widest transition-all duration-150"
          style={{
            color: "#b0b0b0",
            border: "1px solid #3a3a3a",
            fontFamily: "Helvetica Neue, sans-serif",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = "#ffffff"
            e.currentTarget.style.borderColor = "#ffffff"
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = "#b0b0b0"
            e.currentTarget.style.borderColor = "#3a3a3a"
          }}
        >
          <Pencil className="h-3 w-3" />
          Modifica
        </Link>

        <button
          onClick={handleDelete}
          disabled={deleting}
          className="flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-bold uppercase tracking-widest transition-all duration-150 disabled:opacity-50"
          style={{
            color: "#e8241a",
            border: "1px solid #e8241a22",
            fontFamily: "Helvetica Neue, sans-serif",
          }}
          onMouseEnter={(e) => {
            if (!deleting) e.currentTarget.style.background = "#e8241a18"
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "transparent"
          }}
        >
          {deleting ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <Trash2 className="h-3 w-3" />
          )}
          Elimina
        </button>
      </div>
    </div>
  )
}
