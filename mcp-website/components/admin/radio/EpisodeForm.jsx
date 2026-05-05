"use client"

import { useState, useRef } from "react"
import { useRouter } from "next/navigation"
import Image from "next/image"
import { Loader2, X, Upload } from "lucide-react"
import { routes } from "@/config/routes"
import { createEpisode, updateEpisode } from "@/services/admin/radio"
import { formatDuration } from "@/lib/utils/radio"
import { storageBucket } from "@/config/firebase"
import { ref, uploadBytesResumable, getDownloadURL, deleteObject } from "firebase/storage"

/**
 * @param {{
 *   mode: "create" | "edit",
 *   seasons: import('@/types/radio').RadioSeason[],
 *   episode?: import('@/types/radio').RadioEpisode
 * }} props
 */
// Each video entry: { url: string | null, name: string, progress: number, error: string | null }
function makeEntry(url, name = "") {
  return { url, name: name || url?.split("%2F").pop()?.split("?")[0] || "video", progress: 100, error: null }
}

function toDateInputValue(value) {
  if (!value) return ""

  if (typeof value === "string") {
    if (/^\d{4}-\d{2}-\d{2}/.test(value)) return value.slice(0, 10)

    const match = value.match(/^(\d{2})-(\d{2})-(\d{4})$/)
    if (match) return `${match[3]}-${match[2]}-${match[1]}`

    const parsed = new Date(value)
    if (!Number.isNaN(parsed.getTime())) return parsed.toISOString().slice(0, 10)
    return ""
  }

  if (typeof value === "number") {
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime()) ? "" : parsed.toISOString().slice(0, 10)
  }

  if (typeof value === "object") {
    if (typeof value.toDate === "function") {
      const parsed = value.toDate()
      return Number.isNaN(parsed.getTime()) ? "" : parsed.toISOString().slice(0, 10)
    }

    const seconds = value.seconds ?? value._seconds
    if (typeof seconds === "number") {
      return new Date(seconds * 1000).toISOString().slice(0, 10)
    }
  }

  return ""
}

export function EpisodeForm({ mode, seasons, episode }) {
  const router = useRouter()
  const fileInputRef = useRef(null)
  const artworkInputRef = useRef(null)

  // Use a stable ID for storage paths so videos uploaded in create mode
  // are grouped under the same path even before the episode is saved.
  const [tempId] = useState(() => typeof crypto !== "undefined" ? crypto.randomUUID() : String(Date.now()))

  const [soundcloudUrl, setSoundcloudUrl] = useState("")
  const [seasonId, setSeasonId] = useState(episode?.seasonId ?? seasons[0]?.id ?? "")
  const [episodeNumber, setEpisodeNumber] = useState(
    episode?.episodeNumber ? String(episode.episodeNumber) : ""
  )
  const [description, setDescription] = useState(episode?.description ?? "")
  const [videos, setVideos] = useState(
    () => (episode?.videoUrls ?? []).map(u => makeEntry(u))
  )
  const [artwork, setArtwork] = useState(
    () => episode?.customArtworkUrl
      ? { url: episode.customArtworkUrl, name: "artwork", progress: 100, error: null, storagePath: null }
      : null
  )
  const [recordedAt, setRecordedAt] = useState(() => toDateInputValue(episode?.recordedAt))
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const storageId = episode?.id || tempId

  function handlePickVideos(e) {
    const files = Array.from(e.target.files || [])
    e.target.value = ""
    const remaining = 3 - videos.filter(v => !v.error).length
    files.slice(0, remaining).forEach(file => uploadVideo(file))
  }

  function uploadVideo(file) {
    const ext = file.name.split(".").pop() || "mp4"
    const path = `radio/videos/${storageId}/video_${Date.now()}.${ext}`
    const storageRef = ref(storageBucket, path)
    const entry = { url: null, name: file.name, progress: 0, error: null, storagePath: path }

    setVideos(prev => [...prev, entry])

    const task = uploadBytesResumable(storageRef, file)
    task.on(
      "state_changed",
      snap => {
        const pct = Math.round((snap.bytesTransferred / snap.totalBytes) * 100)
        setVideos(prev => prev.map(v => v.storagePath === path ? { ...v, progress: pct } : v))
      },
      err => {
        setVideos(prev => prev.map(v => v.storagePath === path ? { ...v, error: "Upload fallito" } : v))
      },
      async () => {
        const url = await getDownloadURL(task.snapshot.ref)
        setVideos(prev => prev.map(v => v.storagePath === path ? { ...v, url, progress: 100 } : v))
      }
    )
  }

  async function removeVideo(idx) {
    const v = videos[idx]
    setVideos(prev => prev.filter((_, i) => i !== idx))
    if (v.storagePath) {
      try { await deleteObject(ref(storageBucket, v.storagePath)) } catch {}
    }
  }

  function handlePickArtwork(e) {
    const file = e.target.files?.[0]
    e.target.value = ""
    if (file) uploadArtwork(file)
  }

  function uploadArtwork(file) {
    const ext = file.name.split(".").pop() || "jpg"
    const path = `radio/artwork/${storageId}/artwork_${Date.now()}.${ext}`
    const storageRef = ref(storageBucket, path)

    setArtwork({ url: null, name: file.name, progress: 0, error: null, storagePath: path })

    const task = uploadBytesResumable(storageRef, file)
    task.on(
      "state_changed",
      snap => {
        const pct = Math.round((snap.bytesTransferred / snap.totalBytes) * 100)
        setArtwork(prev => prev?.storagePath === path ? { ...prev, progress: pct } : prev)
      },
      () => {
        setArtwork(prev => prev?.storagePath === path ? { ...prev, error: "Upload fallito" } : prev)
      },
      async () => {
        const url = await getDownloadURL(task.snapshot.ref)
        setArtwork(prev => prev?.storagePath === path ? { ...prev, url, progress: 100 } : prev)
      }
    )
  }

  async function removeArtwork() {
    if (artwork?.storagePath) {
      try { await deleteObject(ref(storageBucket, artwork.storagePath)) } catch {}
    }
    setArtwork(null)
  }

  const uploading = videos.some(v => v.progress < 100 && !v.error) || (artwork && artwork.progress < 100 && !artwork.error)

  async function handleSubmit(e) {
    e.preventDefault()
    if (uploading) return
    setError(null)
    setLoading(true)

    const cleanVideos = videos.filter(v => v.url && !v.error).map(v => v.url)
    const cleanArtwork = artwork?.url && !artwork.error ? artwork.url : null

    const payload = {
      seasonId,
      episodeNumber: parseInt(episodeNumber, 10),
      description: description.trim() || null,
      videoUrls: cleanVideos,
      customArtworkUrl: cleanArtwork,
    }

    if (recordedAt || mode === "create") {
      payload.recordedAt = recordedAt || null
    }

    let res
    if (mode === "create") {
      res = await createEpisode({
        soundcloudUrl: soundcloudUrl.trim(),
        ...payload,
      })
    } else {
      res = await updateEpisode(episode.id, payload)
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

      {/* Custom artwork upload */}
      <div style={fieldGap}>
        <label style={labelStyle}>Artwork personalizzato</label>
        <p style={{ marginBottom: 10, fontSize: 11, color: "#666666", fontFamily: "Helvetica Neue, sans-serif" }}>
          Se non caricato, verrà usato l'artwork di SoundCloud.
        </p>

        {artwork ? (
          <div style={{
            display: "flex", alignItems: "flex-start", gap: 12,
            padding: "12px 14px",
            background: "#111111",
            border: `1px solid ${artwork.error ? "#e8241a44" : artwork.progress < 100 ? "#3a3a3a" : "#2a2a2a"}`,
            borderRadius: 4,
          }}>
            {/* Thumbnail preview */}
            {artwork.url && !artwork.error && (
              <img
                src={artwork.url}
                alt="Artwork"
                style={{ width: 56, height: 56, objectFit: "cover", borderRadius: 4, flexShrink: 0 }}
              />
            )}
            {!artwork.url && !artwork.error && (
              <div style={{ width: 56, height: 56, background: "#1e1e1e", borderRadius: 4, flexShrink: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <span style={{ fontSize: 20 }}>🖼️</span>
              </div>
            )}

            <div style={{ flex: 1, minWidth: 0 }}>
              <p style={{
                margin: 0, fontSize: 13, color: artwork.error ? "#e8241a" : "#ffffff",
                fontFamily: "Helvetica Neue, sans-serif",
                whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
              }}>{artwork.name}</p>
              {artwork.error && (
                <p style={{ margin: "2px 0 0", fontSize: 11, color: "#e8241a", fontFamily: "Helvetica Neue, sans-serif" }}>{artwork.error}</p>
              )}
              {!artwork.error && artwork.progress < 100 && (
                <p style={{ margin: "2px 0 0", fontSize: 11, color: "#666666", fontFamily: "Helvetica Neue, sans-serif" }}>Caricamento {artwork.progress}%…</p>
              )}
              {!artwork.error && artwork.progress === 100 && artwork.url && (
                <a href={artwork.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: "#e8820c", fontFamily: "Helvetica Neue, sans-serif" }}>
                  Anteprima ↗
                </a>
              )}
            </div>

            <button
              type="button"
              onClick={removeArtwork}
              style={{
                flexShrink: 0, width: 30, height: 30,
                display: "flex", alignItems: "center", justifyContent: "center",
                background: "transparent", border: "1px solid #3a3a3a",
                borderRadius: 4, color: "#666666", cursor: "pointer",
              }}
            >
              <X style={{ width: 12, height: 12 }} />
            </button>
          </div>
        ) : (
          <>
            <input
              ref={artworkInputRef}
              type="file"
              accept="image/*"
              style={{ display: "none" }}
              onChange={handlePickArtwork}
            />
            <button
              type="button"
              onClick={() => artworkInputRef.current?.click()}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "10px 16px",
                background: "transparent",
                border: "1px dashed #3a3a3a",
                borderRadius: 4,
                color: "#b0b0b0",
                fontSize: 11, fontWeight: 700,
                textTransform: "uppercase", letterSpacing: "0.1em",
                fontFamily: "Helvetica Neue, sans-serif",
                cursor: "pointer", width: "100%", justifyContent: "center",
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "#e8820c"; e.currentTarget.style.color = "#e8820c" }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#3a3a3a"; e.currentTarget.style.color = "#b0b0b0" }}
            >
              <Upload style={{ width: 14, height: 14 }} />
              Carica artwork
            </button>
          </>
        )}

        {/* SoundCloud artwork fallback preview */}
        {mode === "edit" && episode?.soundcloudArtworkUrl && !artwork && (
          <div style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 10 }}>
            <img
              src={episode.soundcloudArtworkUrl}
              alt="SoundCloud artwork"
              style={{ width: 40, height: 40, objectFit: "cover", borderRadius: 3, opacity: 0.5 }}
            />
            <p style={{ margin: 0, fontSize: 11, color: "#666666", fontFamily: "Helvetica Neue, sans-serif" }}>
              Artwork attuale da SoundCloud (verrà usato come fallback)
            </p>
          </div>
        )}
      </div>

      {/* Video upload */}
      <div style={fieldGap}>
        <label style={labelStyle}>Video (max 3)</label>

        {/* Uploaded / uploading list */}
        {videos.length > 0 && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 10 }}>
            {videos.map((v, idx) => (
              <div key={idx} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "10px 12px",
                background: "#111111",
                border: `1px solid ${v.error ? "#e8241a44" : v.progress < 100 ? "#3a3a3a" : "#2a2a2a"}`,
                borderRadius: 4,
              }}>
                {/* Progress bar background */}
                {v.progress < 100 && !v.error && (
                  <div style={{
                    position: "absolute", left: 0, top: 0, bottom: 0,
                    width: `${v.progress}%`,
                    background: "rgba(232,130,12,0.08)",
                    borderRadius: 4,
                    pointerEvents: "none",
                  }} />
                )}
                <span style={{ fontSize: 16 }}>{v.error ? "⚠️" : v.progress < 100 ? "⏳" : "🎬"}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    margin: 0, fontSize: 13, color: v.error ? "#e8241a" : "#ffffff",
                    fontFamily: "Helvetica Neue, sans-serif",
                    whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                  }}>{v.name}</p>
                  {v.error && (
                    <p style={{ margin: "2px 0 0", fontSize: 11, color: "#e8241a", fontFamily: "Helvetica Neue, sans-serif" }}>{v.error}</p>
                  )}
                  {!v.error && v.progress < 100 && (
                    <p style={{ margin: "2px 0 0", fontSize: 11, color: "#666666", fontFamily: "Helvetica Neue, sans-serif" }}>Caricamento {v.progress}%…</p>
                  )}
                  {!v.error && v.progress === 100 && v.url && (
                    <a href={v.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: "#e8820c", fontFamily: "Helvetica Neue, sans-serif" }}>
                      Anteprima ↗
                    </a>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => removeVideo(idx)}
                  style={{
                    flexShrink: 0, width: 30, height: 30,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: "transparent", border: "1px solid #3a3a3a",
                    borderRadius: 4, color: "#666666", cursor: "pointer",
                  }}
                >
                  <X style={{ width: 12, height: 12 }} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Upload button */}
        {videos.filter(v => !v.error).length < 3 && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept="video/*"
              multiple
              style={{ display: "none" }}
              onChange={handlePickVideos}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "10px 16px",
                background: "transparent",
                border: "1px dashed #3a3a3a",
                borderRadius: 4,
                color: "#b0b0b0",
                fontSize: 11, fontWeight: 700,
                textTransform: "uppercase", letterSpacing: "0.1em",
                fontFamily: "Helvetica Neue, sans-serif",
                cursor: "pointer", width: "100%", justifyContent: "center",
              }}
              onMouseEnter={e => { e.currentTarget.style.borderColor = "#e8820c"; e.currentTarget.style.color = "#e8820c" }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = "#3a3a3a"; e.currentTarget.style.color = "#b0b0b0" }}
            >
              <Upload style={{ width: 14, height: 14 }} />
              Carica video
            </button>
          </>
        )}
        <p style={{ marginTop: 6, fontSize: 11, color: "#666666", fontFamily: "Helvetica Neue, sans-serif" }}>
          MP4, MOV, WebM — max 3 video. Il file viene caricato su Firebase Storage.
        </p>
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
          disabled={loading || uploading}
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
            cursor: loading || uploading ? "not-allowed" : "pointer",
            opacity: loading || uploading ? 0.6 : 1,
          }}
        >
          {(loading || uploading) && <Loader2 style={{ width: 14, height: 14 }} className="animate-spin" />}
          {uploading ? "Caricamento in corso…" : mode === "edit" ? "Aggiorna" : "Crea episodio"}
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
