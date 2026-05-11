import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import Link from "next/link"
import { endpoints, getServerBaseUrl } from "@/config/endpoints"

const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const BF = 'Charter, Georgia, "Times New Roman", serif'

// ── JWT helpers ───────────────────────────────────────────────────────────────

function decodeJwtClaims(token) {
  try {
    const payload = token.split(".")[1]
    const json = Buffer.from(payload, "base64url").toString("utf8")
    return JSON.parse(json)
  } catch {
    return {}
  }
}

// ── Server-side fetchers ──────────────────────────────────────────────────────

async function fetchGuide(slug) {
  try {
    const url = `${endpoints.getEventGuide}?slug=${encodeURIComponent(slug)}`
    const res = await fetch(url, { cache: "no-store" })
    if (!res.ok) return null
    const data = await res.json()
    return data?.error ? null : data
  } catch {
    return null
  }
}

async function fetchTicket(eventId, token) {
  try {
    const url = `${endpoints.member.ticket}?event_id=${encodeURIComponent(eventId)}`
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
    if (res.status === 401) return { expired: true }
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

async function fetchLocation(eventId, token) {
  try {
    const url = `${endpoints.member.getEventLocation}?event_id=${encodeURIComponent(eventId)}`
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

// ── UI components (pure, no hooks) ───────────────────────────────────────────

function fmt(dateStr) {
  if (!dateStr) return ""
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric" })
}

function Logo() {
  return (
    <Link href="/" style={{ textDecoration: "none", display: "inline-block", marginBottom: "2.5rem" }}>
      <span style={{ fontFamily: HN, fontWeight: 900, fontSize: "0.875rem", color: "#E07800", letterSpacing: "0.32em", textTransform: "uppercase" }}>MCP</span>
    </Link>
  )
}

function SectionBlock({ section }) {
  const isWarning = section.type === "warning"
  const isChecklist = section.type === "checklist"
  const lines = (section.content || "").split("\n")
  return (
    <div style={{ marginBottom: "2.25rem" }}>
      <h3 className="guide-section-label">{isWarning ? "⚠ " : ""}{section.title}</h3>
      {isChecklist ? (
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {lines.map((line, i) => {
            const text = line.startsWith("- ") ? line.slice(2) : line
            return text ? (
              <li key={i} style={{ display: "flex", gap: "0.75rem", alignItems: "flex-start" }}>
                <span style={{ color: "#E07800", marginTop: "0.2em", flexShrink: 0 }}>—</span>
                <span style={{ fontFamily: BF, fontSize: "1rem", color: "#c8c8c8", lineHeight: 1.65 }}>{text}</span>
              </li>
            ) : null
          })}
        </ul>
      ) : (
        <p style={{ fontFamily: BF, fontSize: "1rem", color: "#c8c8c8", margin: 0, lineHeight: 1.75, whiteSpace: "pre-line" }}>
          {section.content}
        </p>
      )}
    </div>
  )
}

function LocationBlock({ location, hint }) {
  return (
    <div style={{ marginBottom: "2.25rem" }}>
      <h3 className="guide-section-label">Location</h3>
      {location.label && (
        <p style={{ fontFamily: HN, fontWeight: 700, fontSize: "1.125rem", color: "#ffffff", margin: "0 0 0.375rem 0", textTransform: "uppercase", letterSpacing: "-0.01em" }}>
          {location.label}
        </p>
      )}
      {(hint || location.hint) && (
        <p style={{ fontFamily: BF, fontSize: "0.9375rem", color: "rgba(255,255,255,0.45)", margin: "0 0 0.625rem 0", lineHeight: 1.6 }}>
          {hint || location.hint}
        </p>
      )}
      {location.address && (
        <p style={{ fontFamily: BF, fontSize: "0.9375rem", color: "#c8c8c8", margin: "0 0 1rem 0" }}>
          {location.address}
        </p>
      )}
      {location.maps_url && (
        <a href={location.maps_url} target="_blank" rel="noreferrer" style={{ fontFamily: HN, fontWeight: 700, fontSize: "0.5625rem", letterSpacing: "0.22em", textTransform: "uppercase", color: "#E07800", textDecoration: "none" }}>
          Apri in Google Maps →
        </a>
      )}
      {location.maps_embed_url && (
        <div style={{ marginTop: "1.25rem", borderRadius: "2px", overflow: "hidden", border: "1px solid #1a1a1a" }}>
          <iframe src={location.maps_embed_url} width="100%" height="260" style={{ border: "none", display: "block" }} loading="lazy" title="Mappa evento" allowFullScreen />
        </div>
      )}
    </div>
  )
}

// ── Access-denied screens ─────────────────────────────────────────────────────

function AccessDeniedScreen({ title, message, cta }) {
  return (
    <div className="guide-page">
      <Logo />
      <p style={{ fontFamily: HN, fontWeight: 700, fontSize: "0.5625rem", letterSpacing: "0.28em", textTransform: "uppercase", color: "#E07800", margin: "0 0 0.875rem 0" }}>Guide</p>
      {title && (
        <h1 style={{ fontFamily: HN, fontWeight: 900, fontSize: "clamp(2rem, 5vw, 2.75rem)", color: "#ffffff", margin: "0 0 2rem 0", lineHeight: 1.1, letterSpacing: "-0.02em", textTransform: "uppercase" }}>
          {title}
        </h1>
      )}
      <hr className="guide-divider" />
      <p style={{ fontFamily: HN, fontSize: "0.8125rem", color: "rgba(255,255,255,0.35)", marginTop: "2rem", letterSpacing: "0.04em" }}>
        {cta}
      </p>
      {message && (
        <p style={{ fontFamily: HN, fontSize: "0.75rem", color: "rgba(255,255,255,0.2)", marginTop: "0.75rem", letterSpacing: "0.04em" }}>
          {message}
        </p>
      )}
    </div>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default async function EventGuidePage({ params }) {
  const { slug } = await params

  // 1. Read token from cookie (middleware already blocked if missing)
  const cookieStore = await cookies()
  const token = cookieStore.get("mcp_auth_token")?.value
  if (!token) redirect(`/login?redirect=/events/${slug}/guide`)

  // 2. Decode JWT claims (no crypto verification — the backend does that)
  const claims = decodeJwtClaims(token)
  const isAdmin = !!claims?.admin

  // 3. Fetch guide (public)
  const guide = await fetchGuide(slug)
  if (!guide) {
    return (
      <AccessDeniedScreen
        cta="La guide per questo evento non è ancora disponibile."
      />
    )
  }

  const { event_id, event_title, event_date, event_start_time, location_hint, lineup, guide: guideData } = guide

  // 4. Check access
  let ticket = null
  if (!isAdmin) {
    const ticketResult = await fetchTicket(event_id, token)

    // Token scaduto: il client si deve ri-autenticare
    if (ticketResult?.expired) {
      redirect(`/login?redirect=/events/${slug}/guide`)
    }

    if (!ticketResult?.is_participant) {
      return (
        <AccessDeniedScreen
          title={event_title}
          cta="Non hai acquistato la partecipazione a questo evento"
        />
      )
    }
    ticket = ticketResult
  }

  // 5. Fetch location (non-blocking: se non disponibile si mostra solo location_hint)
  const location = await fetchLocation(event_id, token)

  // 6. Render full guide
  const { sections } = guideData

  return (
    <div className="guide-page">
      <Logo />

      <div style={{ marginBottom: "2rem" }}>
        <p style={{ fontFamily: HN, fontWeight: 700, fontSize: "0.5625rem", letterSpacing: "0.28em", textTransform: "uppercase", color: "#E07800", margin: "0 0 0.875rem 0" }}>Guide</p>
        <h1 style={{ fontFamily: HN, fontWeight: 900, fontSize: "clamp(2rem, 5vw, 2.75rem)", color: "#ffffff", margin: "0 0 0.5rem 0", lineHeight: 1.1, letterSpacing: "-0.02em", textTransform: "uppercase" }}>
          {event_title}
        </h1>
        <p style={{ fontFamily: HN, fontWeight: 300, fontSize: "0.75rem", letterSpacing: "0.18em", color: "#E07800", margin: "0 0 0.625rem 0", textTransform: "uppercase" }}>
          {fmt(event_date)}{event_start_time ? ` · ${event_start_time}` : ""}
        </p>
        {lineup?.length > 0 && (
          <p style={{ fontFamily: BF, fontSize: "0.9375rem", color: "rgba(255,255,255,0.38)", margin: 0 }}>
            {lineup.join(", ")}
          </p>
        )}
      </div>

      <hr className="guide-divider" />

      {location ? (
        <>
          <LocationBlock location={location} hint={location_hint} />
          <hr className="guide-divider" />
        </>
      ) : location_hint ? (
        <>
          <div style={{ marginBottom: "2.25rem" }}>
            <h3 className="guide-section-label">Location</h3>
            <p style={{ fontFamily: BF, fontSize: "0.9375rem", color: "rgba(255,255,255,0.45)", lineHeight: 1.6 }}>{location_hint}</p>
          </div>
          <hr className="guide-divider" />
        </>
      ) : null}

      {sections?.map((s) => (
        <SectionBlock key={s.id} section={s} />
      ))}

      {(ticket?.ticket_pdf_url || ticket?.wallet_url) && (
        <>
          <hr className="guide-divider" />
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {ticket.ticket_pdf_url && (
              <a href={ticket.ticket_pdf_url} target="_blank" rel="noreferrer" className="auth-btn" style={{ display: "inline-block", width: "auto", padding: "0.875rem 2rem" }}>
                Scarica il tuo invito (PDF) →
              </a>
            )}
            {ticket.wallet_url && (
              <a href={ticket.wallet_url} target="_blank" rel="noreferrer" className="dash-outline-btn" style={{ display: "inline-block", width: "auto", padding: "0.875rem 2rem" }}>
                Aggiungi al Wallet →
              </a>
            )}
          </div>
        </>
      )}
    </div>
  )
}
