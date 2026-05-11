"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import {
  getMemberProfile,
  getMemberEvents,
  getMemberPurchases,
  getMemberTicket,
  updateMemberPreferences,
} from "@/services/member/memberService"
import { safePublicFetch } from "@/lib/fetch"
import { endpoints } from "@/config/endpoints"
import { getImageUrl } from "@/config/firebaseStorage"

const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const BF = 'Charter, Georgia, "Times New Roman", serif'

function fmt(dateStr) {
  if (!dateStr) return ""
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit", year: "numeric" })
}

function fmtCurrency(amount, currency) {
  const num = parseFloat(amount)
  if (isNaN(num)) return amount || ""
  const cur = (currency || "EUR").toUpperCase()
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: cur }).format(num)
}

function SectionLabel({ children }) {
  return <h2 className="dash-section-label">{children}</h2>
}

function EventCard({ ev }) {
  const [imgUrl, setImgUrl] = useState(null)

  useEffect(() => {
    if (!ev.image) return
    getImageUrl("events", `${ev.image}.jpg`).then(url => {
      if (url) setImgUrl(url)
    })
  }, [ev.image])

  return (
    <div style={{
      display: "flex",
      gap: "1rem",
      alignItems: "stretch",
      background: "#0c0c0c",
      border: "1px solid #1a1a1a",
      borderRadius: "2px",
      overflow: "hidden",
    }}>
      <div style={{ width: "72px", flexShrink: 0, background: "#111", position: "relative", overflow: "hidden" }}>
        {imgUrl ? (
          <img src={imgUrl} alt={ev.title} style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
        ) : (
          <div style={{ width: "100%", minHeight: "72px", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ fontFamily: HN, fontWeight: 900, fontSize: "0.6rem", color: "rgba(224,120,0,0.2)", letterSpacing: "0.1em" }}>MCP</span>
          </div>
        )}
      </div>
      <div style={{ flex: 1, padding: "0.875rem 1rem 0.875rem 0", display: "flex", flexDirection: "column", justifyContent: "center", gap: "0.3rem" }}>
        <p style={{ fontFamily: HN, fontWeight: 700, fontSize: "0.875rem", color: "#ffffff", margin: 0, letterSpacing: "-0.01em", textTransform: "uppercase" }}>
          {ev.title}
        </p>
        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontFamily: HN, fontWeight: 300, fontSize: "0.625rem", letterSpacing: "0.18em", color: "#E07800", textTransform: "uppercase" }}>
            {fmt(ev.date)}
          </span>
          {ev.location_hint && (
            <span style={{ fontFamily: HN, fontWeight: 300, fontSize: "0.625rem", letterSpacing: "0.12em", color: "rgba(255,255,255,0.28)", textTransform: "uppercase" }}>
              {ev.location_hint}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const [member, setMember] = useState(null)
  const [nextEvent, setNextEvent] = useState(null)
  const [ticket, setTicket] = useState(null)
  const [memberEvents, setMemberEvents] = useState(null)
  const [purchases, setPurchases] = useState(null)
  const [loadingMain, setLoadingMain] = useState(true)
  const [loadingEvents, setLoadingEvents] = useState(false)
  const [loadingPurchases, setLoadingPurchases] = useState(false)
  const [preferenceSaving, setPreferenceSaving] = useState(false)
  const [preferenceMsg, setPreferenceMsg] = useState("")
  const [newsletterConsent, setNewsletterConsent] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => { loadInitialData() }, [])

  async function loadInitialData() {
    setLoadingMain(true)
    const [profileResult, eventResult] = await Promise.all([
      getMemberProfile(),
      safePublicFetch(endpoints.getNextEvent),
    ])
    if (profileResult.error) {
      setError(profileResult.error)
      setLoadingMain(false)
      return
    }
    setMember(profileResult)
    setNewsletterConsent(profileResult.newsletter_consent ?? true)
    const events = eventResult?.data
    const ev = Array.isArray(events) ? events[0] : null
    setNextEvent(ev || null)
    if (ev?.id) {
      const ticketResult = await getMemberTicket(ev.id)
      if (!ticketResult.error) setTicket(ticketResult)
    }
    setLoadingMain(false)
  }

  const loadMemberEvents = useCallback(async () => {
    if (memberEvents !== null) return
    setLoadingEvents(true)
    const result = await getMemberEvents()
    setMemberEvents(Array.isArray(result) ? result : [])
    setLoadingEvents(false)
  }, [memberEvents])

  const loadPurchases = useCallback(async () => {
    if (purchases !== null) return
    setLoadingPurchases(true)
    const result = await getMemberPurchases()
    setPurchases(Array.isArray(result) ? result : [])
    setLoadingPurchases(false)
  }, [purchases])

  async function savePreferences() {
    setPreferenceSaving(true)
    setPreferenceMsg("")
    const result = await updateMemberPreferences(newsletterConsent)
    setPreferenceSaving(false)
    if (result.error) {
      setPreferenceMsg("Errore nel salvataggio.")
    } else {
      setPreferenceMsg("Preferenze aggiornate.")
    }
  }

  if (loadingMain) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "40vh" }}>
        <div style={{
          width: "24px",
          height: "24px",
          border: "2px solid #1a1a1a",
          borderTopColor: "#E07800",
          borderRadius: "50%",
          animation: "spin 0.75s linear infinite",
        }} />
      </div>
    )
  }

  if (error) {
    return (
      <p style={{ fontFamily: HN, fontSize: "0.8125rem", color: "#D10000", letterSpacing: "0.04em" }}>{error}</p>
    )
  }

  const currentYear = new Date().getFullYear()

  return (
    <div>
      {/* ── Membership card ── */}
      <div className="member-card">
        <div className="member-card-wm">MCP</div>

        <div style={{ marginBottom: "1.25rem" }}>
          <span style={{
            fontFamily: HN,
            fontWeight: 700,
            fontSize: "0.5rem",
            letterSpacing: "0.28em",
            textTransform: "uppercase",
            color: member?.subscription_valid ? "#E07800" : "#3a3a3a",
            border: `1px solid ${member?.subscription_valid ? "rgba(224,120,0,0.5)" : "#2a2a2a"}`,
            borderRadius: "2px",
            padding: "0.25rem 0.625rem",
          }}>
            {member?.subscription_valid ? "Tessera attiva" : "Tessera scaduta"}
          </span>
        </div>

        <h1 style={{
          fontFamily: HN,
          fontWeight: 900,
          fontSize: "clamp(1.5rem, 4vw, 2rem)",
          color: "#ffffff",
          margin: "0 0 0.375rem 0",
          letterSpacing: "-0.01em",
          textTransform: "uppercase",
        }}>
          {[member?.name, member?.surname].filter(Boolean).join(" ") || ""}
        </h1>

        {member?.end_date && (
          <p style={{
            fontFamily: HN,
            fontWeight: 300,
            fontSize: "0.75rem",
            letterSpacing: "0.14em",
            color: "rgba(255,255,255,0.3)",
            margin: "0 0 1.5rem 0",
            textTransform: "uppercase",
          }}>
            Valida fino al {fmt(member.end_date)}
          </p>
        )}

        <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
          {member?.card_url ? (
            <a href={member.card_url} target="_blank" rel="noreferrer" className="dash-outline-btn">
              Scarica tessera →
            </a>
          ) : (
            <span style={{
              fontFamily: HN,
              fontSize: "0.6875rem",
              letterSpacing: "0.1em",
              color: "rgba(255,255,255,0.18)",
              textTransform: "uppercase",
            }}>Tessera non disponibile</span>
          )}
          {member?.wallet_url && (
            <a href={member.wallet_url} target="_blank" rel="noreferrer" className="dash-outline-btn">
              Aggiungi al Wallet →
            </a>
          )}
        </div>
      </div>

      {/* ── Next event ── */}
      {nextEvent && (
        <div className="dash-section">
          <SectionLabel>Prossimo evento</SectionLabel>
          <div className="dash-event-card">
            <p style={{
              fontFamily: HN,
              fontWeight: 900,
              fontSize: "1.125rem",
              color: "#ffffff",
              margin: "0 0 0.375rem 0",
              letterSpacing: "-0.01em",
              textTransform: "uppercase",
            }}>
              {nextEvent.title}
            </p>
            <p style={{
              fontFamily: HN,
              fontWeight: 300,
              fontSize: "0.75rem",
              letterSpacing: "0.14em",
              color: "#E07800",
              margin: "0 0 1.25rem 0",
              textTransform: "uppercase",
            }}>
              {fmt(nextEvent.date)}{nextEvent.startTime ? ` · ${nextEvent.startTime}` : ""}
            </p>
            {ticket?.is_participant ? (
              <Link href={`/events/${nextEvent.slug}/guide`} className="dash-cta-btn">
                Get ready → {nextEvent.title}
              </Link>
            ) : (
              <Link href={`/events/${nextEvent.slug}`} className="dash-outline-btn">
                Compra partecipazione →
              </Link>
            )}
          </div>
        </div>
      )}

      {/* ── Events attended ── */}
      <div className="dash-section">
        <SectionLabel>Eventi a cui hai partecipato</SectionLabel>
        {memberEvents === null ? (
          <button onClick={loadMemberEvents} className="dash-load-btn" disabled={loadingEvents}>
            {loadingEvents ? "Caricamento…" : "Mostra"}
          </button>
        ) : memberEvents.length === 0 ? (
          <p style={{ fontFamily: HN, fontSize: "0.75rem", letterSpacing: "0.08em", color: "rgba(255,255,255,0.2)", textTransform: "uppercase" }}>
            Nessun evento registrato
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {memberEvents.map((ev) => (
              <EventCard key={ev.id} ev={ev} />
            ))}
          </div>
        )}
      </div>

      {/* ── Purchases ── */}
      <div className="dash-section">
        <SectionLabel>I tuoi acquisti</SectionLabel>
        {purchases === null ? (
          <button onClick={loadPurchases} className="dash-load-btn" disabled={loadingPurchases}>
            {loadingPurchases ? "Caricamento…" : "Mostra"}
          </button>
        ) : purchases.length === 0 ? (
          <p style={{ fontFamily: HN, fontSize: "0.75rem", letterSpacing: "0.08em", color: "rgba(255,255,255,0.2)", textTransform: "uppercase" }}>
            Nessun acquisto registrato
          </p>
        ) : (
          <div>
            {purchases.map((p) => (
              <div key={p.id} className="dash-row">
                <span style={{ fontFamily: BF, color: "#d0d0d0", fontSize: "0.9375rem" }}>
                  {p.event_title || (p.type === "membership" ? "Tessera" : p.type)}
                </span>
                <span style={{ fontFamily: HN, color: "rgba(255,255,255,0.28)", fontSize: "0.6875rem", letterSpacing: "0.1em", whiteSpace: "nowrap" }}>
                  {fmtCurrency(p.amount_total, p.currency)} · {fmt(p.timestamp)}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── Renewals ── */}
      <div className="dash-section">
        <SectionLabel>Storico rinnovi</SectionLabel>
        {(member?.renewals?.length > 0) ? (
          <div>
            {[...(member.renewals)].sort((a, b) => (a.year || 0) - (b.year || 0)).map((r) => (
              <div key={r.year} className="dash-row">
                <span style={{
                  fontFamily: HN,
                  fontWeight: r.year === currentYear ? 700 : 300,
                  fontSize: "0.875rem",
                  letterSpacing: "0.1em",
                  color: r.year === currentYear ? "#E07800" : "rgba(255,255,255,0.5)",
                  textTransform: "uppercase",
                }}>
                  {r.year}
                  {r.year === currentYear && (
                    <span style={{
                      marginLeft: "0.75rem",
                      fontSize: "0.5rem",
                      letterSpacing: "0.22em",
                      border: "1px solid rgba(224,120,0,0.4)",
                      borderRadius: "2px",
                      padding: "0.125rem 0.375rem",
                      verticalAlign: "middle",
                    }}>Attivo</span>
                  )}
                </span>
                {r.fee != null && (
                  <span style={{ fontFamily: HN, color: "rgba(255,255,255,0.28)", fontSize: "0.6875rem", letterSpacing: "0.1em" }}>
                    {r.fee}€
                  </span>
                )}
              </div>
            ))}
          </div>
        ) : (member?.membership_years?.length > 0) ? (
          <div>
            {member.membership_years.map((y) => (
              <div key={y} className="dash-row">
                <span style={{
                  fontFamily: HN,
                  fontWeight: y === currentYear ? 700 : 300,
                  fontSize: "0.875rem",
                  letterSpacing: "0.1em",
                  color: y === currentYear ? "#E07800" : "rgba(255,255,255,0.5)",
                  textTransform: "uppercase",
                }}>{y}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontFamily: HN, fontSize: "0.75rem", letterSpacing: "0.08em", color: "rgba(255,255,255,0.2)", textTransform: "uppercase" }}>
            Nessun rinnovo registrato
          </p>
        )}
      </div>

      {/* ── Preferences ── */}
      <div className="dash-section">
        <SectionLabel>Preferenze comunicazioni</SectionLabel>
        <label style={{
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          cursor: "pointer",
          marginBottom: "1.5rem",
        }}>
          <input
            type="checkbox"
            checked={newsletterConsent}
            onChange={(e) => setNewsletterConsent(e.target.checked)}
            style={{ width: "16px", height: "16px", accentColor: "#E07800", cursor: "pointer" }}
          />
          <span style={{
            fontFamily: HN,
            fontWeight: 300,
            fontSize: "0.8125rem",
            letterSpacing: "0.06em",
            color: "rgba(255,255,255,0.6)",
          }}>Newsletter MCP</span>
        </label>
        <button
          onClick={savePreferences}
          disabled={preferenceSaving}
          className="auth-btn"
          style={{ maxWidth: "280px" }}
        >
          {preferenceSaving ? "Salvataggio…" : "Salva preferenze"}
        </button>
        {preferenceMsg && (
          <p style={{
            fontFamily: HN,
            fontSize: "0.625rem",
            letterSpacing: "0.2em",
            textTransform: "uppercase",
            color: "#E07800",
            margin: "1rem 0 0 0",
          }}>{preferenceMsg}</p>
        )}
      </div>
    </div>
  )
}
