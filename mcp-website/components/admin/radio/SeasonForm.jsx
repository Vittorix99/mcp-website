"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Loader2 } from "lucide-react"
import { routes } from "@/config/routes"
import { createSeason, updateSeason } from "@/services/admin/radio"

/**
 * @param {{
 *   mode: "create" | "edit",
 *   season?: import('@/types/radio').RadioSeason
 * }} props
 */
export function SeasonForm({ mode, season }) {
  const router = useRouter()
  const [name, setName] = useState(season?.name ?? "")
  const [year, setYear] = useState(season?.year ? String(season.year) : "")
  const [description, setDescription] = useState(season?.description ?? "")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const data = {
      name: name.trim(),
      year: parseInt(year, 10),
      ...(description.trim() ? { description: description.trim() } : {}),
    }

    const res =
      mode === "edit"
        ? await updateSeason(season.id, data)
        : await createSeason(data)

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
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 480 }}>
      {/* Name */}
      <div style={{ marginBottom: 24 }}>
        <label style={labelStyle}>Nome stagione *</label>
        <input
          type="text"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="es. Season 1"
          style={inputStyle}
          onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
          onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
        />
      </div>

      {/* Year */}
      <div style={{ marginBottom: 24 }}>
        <label style={labelStyle}>Anno *</label>
        <input
          type="number"
          required
          min={2000}
          max={2100}
          value={year}
          onChange={(e) => setYear(e.target.value)}
          placeholder="es. 2024"
          style={inputStyle}
          onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
          onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
        />
      </div>

      {/* Description */}
      <div style={{ marginBottom: 32 }}>
        <label style={labelStyle}>Descrizione</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Breve descrizione della stagione (opzionale)"
          rows={3}
          style={{ ...inputStyle, resize: "vertical", lineHeight: 1.6 }}
          onFocus={(e) => (e.target.style.borderColor = "#e8820c")}
          onBlur={(e) => (e.target.style.borderColor = "#3a3a3a")}
        />
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
          {mode === "edit" ? "Aggiorna" : "Crea"}
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
