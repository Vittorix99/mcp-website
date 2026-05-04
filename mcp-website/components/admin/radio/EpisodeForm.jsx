"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { Loader2, Plus, X } from "lucide-react"
import { routes } from "@/config/routes"
import { createEpisode, updateEpisode } from "@/services/admin/radio"
import { formatDuration } from "@/lib/utils/radio"

/**
 * @param {{
 *   mode: "create" | "edit",
 *   seasons: import('@/types/radio').RadioSeason[],
 *   episode?: import('@/types/radio').RadioEpisode
 * }} props
 */
export function EpisodeForm({ mode, seasons, episode }) {
  const router = useRouter()

  const [soundcloudUrl, setSoundcloudUrl] = useState("")
  const [seasonId, setSeasonId] = useState(episode?.seasonId ?? seasons[0]?.id ?? "")
  const [episodeNumber, setEpisodeNumber] = useState(
    episode?.episodeNumber ? String(episode.episodeNumber) : ""
  )
  const [description, setDescription] = useState(episode?.description ?? "")
  const [videoUrls, setVideoUrls] = useState(episode?.videoUrls ?? [""])
  const [recordedAt, setRecordedAt] = useState(
    episode?.recordedAt ? episode.recordedAt.slice(0, 10) : ""
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  function addVideoUrl() {
    if (videoUrls.length < 3) setVideoUrls([...videoUrls, ""])
  }

  function removeVideoUrl(idx) {
    setVideoUrls(videoUrls.filter((_, i) => i !== idx))
  }

  function updateVideoUrl(idx, val) {
    setVideoUrls(videoUrls.map((u, i) => (i === idx ? val : u)))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const cleanVideos = videoUrls.map((u) => u.trim()).filter(Boolean)

    let res
    if (mode === "create") {
      res = await createEpisode({
        soundcloudUrl: soundcloudUrl.trim(),
        seasonId,
        episodeNumber: parseInt(episodeNumber, 10),
        description: description.trim() || null,
        videoUrls: cleanVideos,
        recordedAt: recordedAt || null,
      })
    } else {
      res = await updateEpisode(episode.id, {
        seasonId,
        episodeNumber: parseInt(episodeNumber, 10),
        description: description.trim() || null,
        videoUrls: cleanVideos,
        recordedAt: recordedAt || null,
      })
    }

    if (res?.error) {
      setError(res.error)
      setLoading(false)
      return
    }

    router.push(routes.admin.radio.index)
    router.refresh()
  }

  const labelStyle = {
    display: "block",
    marginBottom: 6,
    fontSize: 11,
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.1em",
    color: "#b0b0b0",
    fontFamily: "Helvetica Neue, sans-serif",
  }

  const inputStyle = {
    width: "100%",
    background: "#111111",
    border: "1px solid #3a3a3a",
    borderRadius: 4,
    padding: "10px 14px",
    color: "#ffffff",
    fontSize: 14,
    fontFamily: "Helvetica Neue, sans-serif",
    outline: "none",
    boxSizing: "border-box",
  }

  const fieldGap = { marginBottom: 24 }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 560 }}>
      {/* SoundCloud URL — create only */}
      {mode === "create" && (
        <div style={fieldGap}>
          <label style={labelStyle}>URL SoundCloud *</label>
          <input
            type="url"
            required
            value={soundcloudUrl}
            onChange={(e) => setSoundcloudUrl(e.target.value)}
            placeholder="https://soundcloud.com/..."
            style={inputStyle}
            onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
            onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
          />
          <p
            style={{
              marginTop: 6,
              fontSize: 12,
              color: "#666666",
              fontFamily: "Helvetica Neue, sans-serif",
            }}
          >
            I metadati (titolo, durata, artwork, generi) verranno importati automaticamente da SoundCloud.
          </p>
        </div>
      )}

      {/* Edit mode: SC info block */}
      {mode === "edit" && episode && (
        <div
          style={{
            marginBottom: 24,
            padding: "14px 16px",
            background: "#0a0a0a",
            border: "1px solid #1e1e1e",
            borderRadius: 6,
            display: "flex",
            gap: 14,
            alignItems: "flex-start",
          }}
        >
          {episode.soundcloudArtworkUrl && (
            <Image
              src={episode.soundcloudArtworkUrl}
              alt={episode.title}
              width={56}
              height={56}
              style={{ borderRadius: 4, flexShrink: 0, width: 56, height: 56, objectFit: "cover" }}
            />
          )}
          <div style={{ minWidth: 0 }}>
            <p
              style={{
                margin: "0 0 4px",
                fontSize: 14,
                fontWeight: 700,
                color: "#ffffff",
                fontFamily: "Helvetica Neue, sans-serif",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {episode.title}
            </p>
            <p style={{ margin: "0 0 4px", fontSize: 12, color: "#b0b0b0", fontFamily: "Helvetica Neue, sans-serif" }}>
              {formatDuration(episode.duration)}
              {episode.genres?.length > 0 && (
                <span style={{ marginLeft: 10 }}>{episode.genres.join(", ")}</span>
              )}
            </p>
            <a
              href={episode.soundcloudUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 11, color: "#e8820c", fontFamily: "Helvetica Neue, sans-serif" }}
            >
              Apri su SoundCloud ↗
            </a>
          </div>
        </div>
      )}

      {/* Season */}
      <div style={fieldGap}>
        <label style={labelStyle}>Stagione *</label>
        <select
          required
          value={seasonId}
          onChange={(e) => setSeasonId(e.target.value)}
          style={{ ...inputStyle, cursor: "pointer" }}
          onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
          onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
        >
          {seasons.map((s) => (
            <option key={s.id} value={s.id} style={{ background: "#111111" }}>
              {s.name} — {s.year}
            </option>
          ))}
        </select>
      </div>

      {/* Episode number */}
      <div style={fieldGap}>
        <label style={labelStyle}>Numero episodio *</label>
        <input
          type="number"
          required
          min={1}
          value={episodeNumber}
          onChange={(e) => setEpisodeNumber(e.target.value)}
          placeholder="es. 1"
          style={inputStyle}
          onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
          onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
        />
      </div>

      {/* Description */}
      <div style={fieldGap}>
        <label style={labelStyle}>Descrizione</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Descrizione opzionale dell'episodio..."
          rows={4}
          style={{ ...inputStyle, resize: "vertical" }}
          onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
          onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
        />
      </div>

      {/* Recorded at */}
      <div style={fieldGap}>
        <label style={labelStyle}>Data registrazione</label>
        <input
          type="date"
          value={recordedAt}
          onChange={(e) => setRecordedAt(e.target.value)}
          style={{ ...inputStyle, colorScheme: "dark" }}
          onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
          onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
        />
      </div>

      {/* Video URLs */}
      <div style={fieldGap}>
        <label style={labelStyle}>Video URL (max 3)</label>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {videoUrls.map((url, idx) => (
            <div key={idx} style={{ display: "flex", gap: 8 }}>
              <input
                type="url"
                value={url}
                onChange={(e) => updateVideoUrl(idx, e.target.value)}
                placeholder="https://..."
                style={{ ...inputStyle, flex: 1 }}
                onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
                onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
              />
              {videoUrls.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeVideoUrl(idx)}
                  style={{
                    flexShrink: 0,
                    width: 38,
                    height: 38,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "transparent",
                    border: "1px solid #3a3a3a",
                    borderRadius: 4,
                    color: "#e8241a",
                    cursor: "pointer",
                  }}
                >
                  <X style={{ width: 14, height: 14 }} />
                </button>
              )}
            </div>
          ))}
        </div>
        {videoUrls.length < 3 && (
          <button
            type="button"
            onClick={addVideoUrl}
            style={{
              marginTop: 8,
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "transparent",
              border: "none",
              color: "#e8820c",
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              fontFamily: "Helvetica Neue, sans-serif",
              cursor: "pointer",
              padding: 0,
            }}
          >
            <Plus style={{ width: 14, height: 14 }} />
            Aggiungi video
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div
          style={{
            marginBottom: 24,
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

      {/* Actions */}
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <button
          type="submit"
          disabled={loading}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "10px 24px",
            background: "#e8820c",
            border: "none",
            borderRadius: 4,
            color: "#000000",
            fontSize: 11,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            fontFamily: "Helvetica Neue, sans-serif",
            cursor: loading ? "not-allowed" : "pointer",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading && <Loader2 style={{ width: 14, height: 14 }} className="animate-spin" />}
          {mode === "edit" ? "Aggiorna" : "Crea episodio"}
        </button>

        <button
          type="button"
          onClick={() => router.push(routes.admin.radio.index)}
          style={{
            padding: "10px 24px",
            background: "transparent",
            border: "1px solid #3a3a3a",
            borderRadius: 4,
            color: "#b0b0b0",
            fontSize: 11,
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.1em",
            fontFamily: "Helvetica Neue, sans-serif",
            cursor: "pointer",
          }}
        >
          Annulla
        </button>
      </div>
    </form>
  )
}
