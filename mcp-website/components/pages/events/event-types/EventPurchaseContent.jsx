"use client"

import { useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"
import Link from "next/link"

import PaymentBlockedWarning from "@/components/warnings/PaymentBlockedWarning"
import QuantitySelector from "@/components/pages/events/QuantitySelector"
import ParticipantsInfoPanel from "@/components/pages/events/ParticipantsInfoPanel"
import { PayPalSection } from "@/components/pages/events/PayPalSection"
import ParticipantsModal from "@/components/pages/events/modals/ParticipantsModal"
import { SelectParticipants } from "@/components/pages/events/SelectParticipants"
import { resolvePurchaseMode, PURCHASE_MODES } from "@/config/events-utils"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const splitLines = (txt = "") =>
  String(txt).replace(/\\n/g, "\n").split("\n").filter((l) => l.trim().length)

const isEventEnded = (event) => (event?.status || "active") === "ended"

const MODE_COPY = {
  [PURCHASE_MODES.PUBLIC]: "L'evento è aperto a tutti i soci e alle nuove richieste di tesseramento.",
  [PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS]:
    "Accesso riservato ai membri già registrati. Inserisci i dati con cui risulti tesserato.",
  [PURCHASE_MODES.ONLY_MEMBERS]:
    "Se un partecipante non è ancora membro, il tesseramento verrà attivato automaticamente con l'acquisto.",
  [PURCHASE_MODES.ON_REQUEST]:
    "Questo evento richiede l'approvazione dello staff. Invia la tua richiesta per ricevere istruzioni.",
}

export default function EventPurchaseContent({ id, event, settings }) {
  const [quantity, setQuantity] = useState(1)
  const [participants, setParticipants] = useState([])
  const [modalOpen, setModalOpen] = useState(false)
  const [formComplete, setFormComplete] = useState(false)
  const [newsletterConsent, setNewsletterConsent] = useState(true)
  const [eventMeta, setEventMeta] = useState({ nonMembers: [] })

  const purchaseMode = resolvePurchaseMode(event)
  const isEnded = isEventEnded(event)
  const paymentBlocked = Boolean(settings?.payment_blocked)
  const iban = settings?.company_iban || ""
  const intestatario = settings?.company_intestatario || ""
  const isOnRequest = purchaseMode === PURCHASE_MODES.ON_REQUEST
  const membershipIncluded = purchaseMode === PURCHASE_MODES.ONLY_MEMBERS

  const cart = useMemo(() => {
    const price = typeof event?.price === "number" ? event.price : 0
    const fee = typeof event?.fee === "number" ? event.fee : 0
    const participantsPayload = newsletterConsent
      ? participants.map((p) => ({ ...p, newsletterConsent: true }))
      : participants
    return {
      eventId: event?.id,
      quantity,
      participants: participantsPayload,
      price,
      fee,
      total: (price + fee) * quantity,
      eventMeta,
      purchaseMode,
    }
  }, [quantity, participants, event, newsletterConsent, eventMeta, purchaseMode])

  if (!event) {
    return (
      <div style={{ minHeight: "200px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Loader2 style={{ width: 24, height: 24, color: ACC }} className="animate-spin" />
      </div>
    )
  }

  return (
    <div style={{ background: "#080808", padding: "64px 0 100px" }}>
      <div style={{ maxWidth: "680px", margin: "0 auto", padding: "0 48px" }}>

        {/* Section label */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "40px" }}>
          <div style={{ width: "36px", height: "1px", background: ACC }} />
          <p style={{
            fontFamily: HN, fontSize: "8px", fontWeight: 700,
            letterSpacing: "0.4em", textTransform: "uppercase",
            color: ACC, margin: 0,
          }}>Acquista</p>
        </div>

        {/* Mode info */}
        {MODE_COPY[purchaseMode] && !isEnded && (
          <p style={{
            fontFamily: CH, fontSize: "15px", fontStyle: "italic",
            lineHeight: 1.75, color: "rgba(245,243,239,0.45)",
            marginBottom: "20px",
          }}>{MODE_COPY[purchaseMode]}</p>
        )}

        {membershipIncluded && (
          <p style={{
            fontFamily: HN, fontSize: "9px", fontWeight: 700,
            letterSpacing: "0.22em", textTransform: "uppercase",
            color: ACC, marginBottom: "28px",
          }}>Tesseramento MCP incluso se non ancora membro</p>
        )}

        {/* Note */}
        {!isEnded && event.note && (
          <div style={{
            padding: "16px 20px",
            background: "rgba(224,120,0,0.06)",
            borderLeft: `2px solid ${ACC}`,
            marginBottom: "28px",
          }}>
            {splitLines(event.note).map((line, i) => (
              <p key={i} style={{
                fontFamily: CH, fontSize: "14px", lineHeight: 1.7,
                color: "rgba(245,243,239,0.6)", margin: "0 0 8px",
              }}>{line}</p>
            ))}
          </div>
        )}

        {/* Statuto */}
        <a
          href="https://drive.google.com/file/d/1IABjzNtUon0Ti32iJMxQdSPkLa4GcdKN/view"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: "inline-block",
            fontFamily: HN, fontSize: "8px", letterSpacing: "0.28em",
            textTransform: "uppercase", color: "rgba(245,243,239,0.3)",
            textDecoration: "none",
            borderBottom: "1px solid rgba(245,243,239,0.12)", paddingBottom: "2px",
            marginBottom: "40px",
          }}
          onMouseEnter={e => e.currentTarget.style.color = "rgba(245,243,239,0.6)"}
          onMouseLeave={e => e.currentTarget.style.color = "rgba(245,243,239,0.3)"}
        >Statuto dell'associazione ↗</a>

        {/* Separator */}
        <div style={{ height: "1px", background: "rgba(245,243,239,0.06)", marginBottom: "40px" }} />

        {/* States */}
        {isEnded ? (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <p style={{
              fontFamily: CH, fontSize: "16px", fontStyle: "italic",
              color: "rgba(245,243,239,0.4)", marginBottom: "24px",
            }}>Evento concluso</p>
            {event.photosReady && (
              <Link
                href={`/events-foto/${event.slug}`}
                style={{
                  display: "inline-block", padding: "12px 32px",
                  background: ACC, borderRadius: "2px",
                  fontFamily: HN, fontWeight: 700, fontSize: "10px",
                  letterSpacing: "0.26em", textTransform: "uppercase",
                  color: "#fff", textDecoration: "none",
                }}
              >Guarda le foto →</Link>
            )}
          </div>
        ) : isOnRequest ? (
          <div style={{
            padding: "24px 28px",
            background: "rgba(224,120,0,0.05)",
            border: "1px solid rgba(224,120,0,0.2)",
          }}>
            <p style={{
              fontFamily: HN, fontSize: "9px", fontWeight: 700,
              letterSpacing: "0.3em", textTransform: "uppercase",
              color: ACC, marginBottom: "12px",
            }}>Evento su richiesta</p>
            <p style={{ fontFamily: CH, fontSize: "15px", lineHeight: 1.7, color: "rgba(245,243,239,0.55)", margin: 0 }}>
              Invia una mail a{" "}
              <a
                href="mailto:info@musicconnectingpeople.org"
                style={{ color: ACC, textDecoration: "none", borderBottom: `1px solid ${ACC}` }}
              >info@musicconnectingpeople.org</a>
              {" "}indicando nome, cognome e motivo dell'interesse.
            </p>
          </div>
        ) : paymentBlocked ? (
          <PaymentBlockedWarning price={event.price ?? 18} iban={iban} intestatario={intestatario} />
        ) : (
          <>
            <QuantitySelector
              quantity={quantity}
              setQuantity={formComplete ? () => {} : setQuantity}
              disabled={formComplete}
            />

            <ParticipantsInfoPanel event={event} purchaseMode={purchaseMode} />

            {formComplete && participants.length === quantity ? (
              <>
                <SelectParticipants participants={participants} />

                <div style={{ marginTop: "24px" }}>
                  <label style={{
                    display: "flex", alignItems: "flex-start", gap: "12px", cursor: "pointer",
                  }}>
                    <input
                      type="checkbox"
                      checked={newsletterConsent}
                      onChange={(e) => setNewsletterConsent(e.target.checked)}
                      style={{ marginTop: "3px", accentColor: ACC, cursor: "pointer" }}
                    />
                    <span style={{
                      fontFamily: CH, fontSize: "13px", lineHeight: 1.6,
                      color: "rgba(245,243,239,0.45)",
                    }}>
                      Acconsento a ricevere comunicazioni promozionali via email, come descritto nella nostra{" "}
                      <a
                        href="https://www.iubenda.com/privacy-policy/78147975"
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "rgba(245,243,239,0.55)", textDecoration: "underline" }}
                      >informativa sulla privacy</a>.
                    </span>
                  </label>
                </div>

                <div style={{ marginTop: "32px" }}>
                  <PayPalSection event={event} cart={cart} purchaseMode={purchaseMode} />
                </div>
              </>
            ) : (
              <ProceedButton onClick={() => setModalOpen(true)} />
            )}
          </>
        )}
      </div>

      {!paymentBlocked && !isOnRequest && (
        <ParticipantsModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          quantity={quantity}
          event={{ ...event, purchase_mode: purchaseMode }}
          eventMeta={eventMeta}
          onEventMetaChange={setEventMeta}
          onSubmit={(data) => {
            if (Array.isArray(data)) {
              setParticipants(data)
              setEventMeta((prev) => prev ?? { nonMembers: [] })
            } else if (data && Array.isArray(data.participants)) {
              setParticipants(data.participants)
              setEventMeta(data.eventMeta ?? { nonMembers: [] })
            } else {
              setEventMeta((prev) => prev ?? { nonMembers: [] })
            }
            setFormComplete(true)
          }}
        />
      )}
    </div>
  )
}

function ProceedButton({ onClick }) {
  const [hov, setHov] = useState(false)
  return (
    <div style={{ marginTop: "32px" }}>
      <button
        onClick={onClick}
        onMouseEnter={() => setHov(true)}
        onMouseLeave={() => setHov(false)}
        style={{
          display: "block", width: "100%", padding: "16px 0",
          background: hov ? "#C96C00" : ACC,
          border: "none", cursor: "pointer", borderRadius: "2px",
          fontFamily: HN, fontWeight: 700, fontSize: "10px",
          letterSpacing: "0.28em", textTransform: "uppercase",
          color: "#fff", transition: "background 0.2s",
        }}
      >Procedi con i dati dei partecipanti →</button>
    </div>
  )
}
