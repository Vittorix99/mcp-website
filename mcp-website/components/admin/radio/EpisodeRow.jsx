"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Pencil, Trash2, Eye, EyeOff, Loader2 } from "lucide-react"
import { TableRow, TableCell } from "@/components/ui/table"
import { routes } from "@/config/routes"
import { deleteEpisode, publishEpisode, unpublishEpisode } from "@/services/admin/radio"
import { formatDuration } from "@/lib/utils/radio"

/**
 * @param {{
 *   episode: import('@/types/radio').RadioEpisode,
 *   seasons: import('@/types/radio').RadioSeason[]
 * }} props
 */
export function EpisodeRow({ episode, seasons }) {
  const router = useRouter()
  const [busy, setBusy] = useState(false)

  const seasonName = seasons.find((s) => s.id === episode.seasonId)?.name ?? "—"

  async function handlePublish() {
    setBusy(true)
    const fn = episode.isPublished ? unpublishEpisode : publishEpisode
    const res = await fn(episode.id)
    if (res?.error) {
      window.dispatchEvent(new CustomEvent("errorToast", { detail: res.error }))
    } else {
      router.refresh()
    }
    setBusy(false)
  }

  async function handleDelete() {
    if (!confirm(`Eliminare l'episodio "${episode.title}"?`)) return
    setBusy(true)
    const res = await deleteEpisode(episode.id)
    if (res?.error) {
      window.dispatchEvent(new CustomEvent("errorToast", { detail: res.error }))
    } else {
      router.refresh()
    }
    setBusy(false)
  }

  return (
    <TableRow style={{ borderColor: "#1e1e1e" }}>
      {/* Artwork */}
      <TableCell className="w-14 py-2 pl-4 pr-2">
        {episode.soundcloudArtworkUrl ? (
          <Image
            src={episode.soundcloudArtworkUrl}
            alt={episode.title}
            width={48}
            height={48}
            className="rounded object-cover"
            style={{ width: 48, height: 48 }}
          />
        ) : (
          <div
            className="rounded"
            style={{ width: 48, height: 48, background: "#1e1e1e" }}
          />
        )}
      </TableCell>

      {/* Episode number */}
      <TableCell className="w-16 py-2">
        <span
          className="text-xs font-black uppercase tracking-widest"
          style={{ color: "#e8820c", fontFamily: "Helvetica Neue, sans-serif" }}
        >
          Ep. {episode.episodeNumber}
        </span>
      </TableCell>

      {/* Title */}
      <TableCell className="max-w-[180px] py-2">
        <span
          className="block truncate text-sm font-medium"
          style={{ color: "#ffffff", fontFamily: "Helvetica Neue, sans-serif" }}
          title={episode.title}
        >
          {episode.title}
        </span>
      </TableCell>

      {/* Season */}
      <TableCell className="py-2">
        <span className="text-xs" style={{ color: "#b0b0b0" }}>
          {seasonName}
        </span>
      </TableCell>

      {/* Duration */}
      <TableCell className="py-2">
        <span className="text-xs" style={{ color: "#b0b0b0" }}>
          {formatDuration(episode.duration)}
        </span>
      </TableCell>

      {/* Genres */}
      <TableCell className="py-2">
        <div className="flex flex-wrap gap-1">
          {(episode.genres || []).map((g) => (
            <span
              key={g}
              className="rounded px-1.5 py-0.5 text-[10px] uppercase tracking-wider"
              style={{ color: "#b0b0b0", border: "1px solid #3a3a3a" }}
            >
              {g}
            </span>
          ))}
        </div>
      </TableCell>

      {/* Status */}
      <TableCell className="py-2">
        {episode.isPublished ? (
          <span
            className="text-xs font-bold uppercase tracking-widest"
            style={{ color: "#22c55e" }}
          >
            • Live
          </span>
        ) : (
          <span
            className="text-xs font-bold uppercase tracking-widest"
            style={{ color: "#3a3a3a" }}
          >
            • Bozza
          </span>
        )}
      </TableCell>

      {/* Actions */}
      <TableCell className="py-2 pr-4">
        <div className="flex items-center gap-1.5">
          <Link
            href={routes.admin.radio.editEpisode(episode.id)}
            className="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-bold uppercase tracking-widest transition-all duration-150"
            style={{ color: "#b0b0b0", border: "1px solid #3a3a3a" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "#fff"
              e.currentTarget.style.borderColor = "#fff"
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
            onClick={handlePublish}
            disabled={busy}
            className="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-bold uppercase tracking-widest transition-all duration-150 disabled:opacity-40"
            style={{
              color: episode.isPublished ? "#b0b0b0" : "#511a6c",
              border: `1px solid ${episode.isPublished ? "#3a3a3a" : "#511a6c"}`,
            }}
          >
            {busy ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : episode.isPublished ? (
              <EyeOff className="h-3 w-3" />
            ) : (
              <Eye className="h-3 w-3" />
            )}
            {episode.isPublished ? "Unpubblica" : "Pubblica"}
          </button>

          <button
            onClick={handleDelete}
            disabled={busy}
            className="flex items-center gap-1 rounded px-2 py-1 text-[11px] font-bold uppercase tracking-widest transition-all duration-150 disabled:opacity-40"
            style={{ color: "#e8241a", border: "1px solid #e8241a22" }}
            onMouseEnter={(e) => {
              if (!busy) e.currentTarget.style.background = "#e8241a18"
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "transparent"
            }}
          >
            <Trash2 className="h-3 w-3" />
            Elimina
          </button>
        </div>
      </TableCell>
    </TableRow>
  )
}
