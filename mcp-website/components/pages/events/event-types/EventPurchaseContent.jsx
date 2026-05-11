"use client"

import { useEffect, useMemo, useState } from "react"
import { CheckCircle2, Loader2, Tag, X } from "lucide-react"
import Link from "next/link"

import PaymentBlockedWarning from "@/components/warnings/PaymentBlockedWarning"
import QuantitySelector from "@/components/pages/events/QuantitySelector"
import ParticipantsInfoPanel from "@/components/pages/events/ParticipantsInfoPanel"
import { PayPalSection } from "@/components/pages/events/PayPalSection"
import ParticipantsModal from "@/components/pages/events/modals/ParticipantsModal"
import { SelectParticipants } from "@/components/pages/events/SelectParticipants"
import { resolvePurchaseMode, PURCHASE_MODES } from "@/config/events-utils"
import { validateDiscountCode } from "@/services/discountCodes"

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

export default function EventPurchaseContent({ id, event, settings, membershipPrice }) {
  const [quantity, setQuantity] = useState(1)
  const [participants, setParticipants] = useState([])
  const [modalOpen, setModalOpen] = useState(false)
  const [formComplete, setFormComplete] = useState(false)
  const [newsletterConsent, setNewsletterConsent] = useState(true)
  const [eventMeta, setEventMeta] = useState({ nonMembers: [] })
  const [discountOpen, setDiscountOpen] = useState(false)
  const [discountCode, setDiscountCode] = useState("")
  const [discountStatus, setDiscountStatus] = useState("idle")
  const [discountCodeId, setDiscountCodeId] = useState(null)
  const [discountAmount, setDiscountAmount] = useState(null)
  const [finalPrice, setFinalPrice] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)

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
    const effectivePrice = discountStatus === "valid" && typeof finalPrice === "number" ? finalPrice : price
    const participantsPayload = newsletterConsent
      ? participants.map((p) => ({ ...p, newsletterConsent: true }))
      : participants
    const payload = {
      eventId: event?.id,
      quantity,
      participants: participantsPayload,
      price: effectivePrice,
      fee,
      total: (effectivePrice + fee) * quantity,
      eventMeta,
      purchaseMode,
    }
    if (discountStatus === "valid" && discountCode) {
      payload.discountCode = discountCode
    }
    return payload
  }, [quantity, participants, event, newsletterConsent, eventMeta, purchaseMode, discountStatus, finalPrice, discountCode, discountCodeId, discountAmount])

  const clearDiscount = (message = null) => {
    setDiscountStatus(message ? "invalid" : "idle")
    setDiscountCodeId(null)
    setDiscountAmount(null)
    setFinalPrice(null)
    setErrorMessage(message)
  }

  useEffect(() => {
    if (discountStatus === "valid" && quantity !== 1) {
      clearDiscount("Codice sconto rimosso — modifica il numero di partecipanti")
    }
  }, [quantity, discountStatus])

  const handleApplyDiscount = async () => {
    const code = discountCode.trim().toUpperCase()
    setDiscountCode(code)
    setErrorMessage(null)

    if (!code) {
      clearDiscount("Inserisci un codice sconto")
      return
    }
    if (quantity !== 1) {
      clearDiscount("Il codice sconto è valido solo per acquisti singoli")
      return
    }

    const payerEmail = participants?.[0]?.email
    if (!payerEmail) {
      clearDiscount("Completa i dati del partecipante prima di applicare il codice")
      return
    }

    setDiscountStatus("loading")
    const result = await validateDiscountCode({
      eventId: event?.id,
      code,
      participantsCount: quantity,
      payerEmail,
    })

    if (!result?.valid) {
      clearDiscount(result?.errorMessage || result?.error_message || "Codice sconto non valido")
      return
    }

    setDiscountStatus("valid")
    setDiscountCodeId(result.discountCodeId || result.discount_code_id || null)
    setDiscountAmount(Number(result.discountAmount ?? result.discount_amount ?? 0))
    setFinalPrice(Number(result.finalPrice ?? result.final_price ?? 0))
    setErrorMessage(null)
  }

  if (!event) {
    return (
      <div style={{ minHeight: "200px", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Loader2 style={{ width: 24, height: 24, color: ACC }} className="animate-spin" />
      </div>
    )
  }

  return (
    <div className="event-purchase-section" style={{ background: "#080808", padding: "64px 0 100px" }}>
      <div className="event-purchase-shell" style={{ maxWidth: "680px", margin: "0 auto", padding: "0 48px" }}>

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

        {/* Price display */}
        {!isEnded && !isOnRequest && (
          <PriceBlock event={event} membershipPrice={membershipPrice} membershipIncluded={membershipIncluded} quantity={quantity} />
        )}

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
                  <DiscountCodePanel
                    open={discountOpen}
                    onToggle={() => setDiscountOpen((value) => !value)}
                    code={discountCode}
                    onCodeChange={(value) => {
                      setDiscountCode(value.toUpperCase())
                      if (discountStatus === "valid") clearDiscount()
                    }}
                    status={discountStatus}
                    errorMessage={errorMessage}
                    discountAmount={discountAmount}
                    onApply={handleApplyDiscount}
                    onRemove={() => {
                      setDiscountCode("")
                      clearDiscount()
                    }}
                  />
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

function formatEuro(value) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(Number(value || 0))
}

function DiscountCodePanel({
  open,
  onToggle,
  code,
  onCodeChange,
  status,
  errorMessage,
  discountAmount,
  onApply,
  onRemove,
}) {
  const isLoading = status === "loading"
  const isValid = status === "valid"
  const isInvalid = status === "invalid" && errorMessage

  return (
    <div style={{ marginBottom: "18px", borderTop: "1px solid rgba(245,243,239,0.08)", paddingTop: "18px" }}>
      <button
        type="button"
        onClick={onToggle}
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          background: "transparent",
          border: 0,
          padding: 0,
          cursor: "pointer",
          color: "#F5F3EF",
          fontFamily: HN,
          fontSize: "10px",
          fontWeight: 800,
          letterSpacing: "0.22em",
          textTransform: "uppercase",
        }}
      >
        <span style={{ display: "inline-flex", alignItems: "center", gap: "9px" }}>
          <Tag style={{ width: 15, height: 15, color: ACC }} />
          Hai un codice sconto?
        </span>
        <span style={{ color: "rgba(245,243,239,0.42)" }}>{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div style={{ marginTop: "14px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: "10px" }}>
            <input
              value={code}
              onChange={(event) => onCodeChange(event.target.value)}
              placeholder="CODICE"
              disabled={isLoading || isValid}
              style={{
                minWidth: 0,
                height: "44px",
                background: "rgba(245,243,239,0.04)",
                border: "1px solid rgba(245,243,239,0.12)",
                color: "#F5F3EF",
                padding: "0 12px",
                fontFamily: HN,
                fontSize: "13px",
                fontWeight: 800,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                outline: "none",
              }}
            />
            {isValid ? (
              <button
                type="button"
                onClick={onRemove}
                aria-label="Rimuovi codice sconto"
                style={{
                  width: "44px",
                  height: "44px",
                  display: "grid",
                  placeItems: "center",
                  background: "rgba(245,243,239,0.04)",
                  border: "1px solid rgba(245,243,239,0.12)",
                  color: "rgba(245,243,239,0.72)",
                  cursor: "pointer",
                }}
              >
                <X style={{ width: 17, height: 17 }} />
              </button>
            ) : (
              <button
                type="button"
                onClick={onApply}
                disabled={isLoading}
                style={{
                  height: "44px",
                  padding: "0 18px",
                  background: isLoading ? "rgba(224,120,0,0.4)" : ACC,
                  border: 0,
                  color: "#fff",
                  fontFamily: HN,
                  fontSize: "9px",
                  fontWeight: 800,
                  letterSpacing: "0.18em",
                  textTransform: "uppercase",
                  cursor: isLoading ? "default" : "pointer",
                }}
              >
                {isLoading ? <Loader2 style={{ width: 16, height: 16 }} className="animate-spin" /> : "Applica"}
              </button>
            )}
          </div>

          {isValid && (
            <div style={{ marginTop: "10px", display: "flex", alignItems: "center", gap: "8px", color: "#9ee6b2", fontFamily: CH, fontSize: "13px" }}>
              <CheckCircle2 style={{ width: 16, height: 16 }} />
              <span>Codice {code} applicato — −{formatEuro(discountAmount)}</span>
            </div>
          )}

          {isInvalid && (
            <p style={{ margin: "10px 0 0", color: "#ffb6b6", fontFamily: CH, fontSize: "13px", lineHeight: 1.45 }}>
              {errorMessage}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function PriceBlock({ event, membershipPrice, membershipIncluded, quantity }) {
  const price = typeof event?.price === "number" ? event.price : 0
  const fee = typeof event?.fee === "number" ? event.fee : 0
  const total = (price + fee) * quantity

  if (price === 0 && fee === 0) return null

  return (
    <div style={{ marginBottom: "32px" }}>
      {/* Membership badge */}
      {membershipIncluded && (
        <p style={{
          fontFamily: HN, fontSize: "8px", fontWeight: 700,
          letterSpacing: "0.3em", textTransform: "uppercase",
          color: ACC, marginBottom: "12px",
        }}>Tessera MCP inclusa per i nuovi soci</p>
      )}

      {/* Base price row */}
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: fee > 0 ? "8px" : "0" }}>
        <span style={{
          fontFamily: HN, fontSize: "9px", fontWeight: 700,
          letterSpacing: "0.3em", textTransform: "uppercase",
          color: "rgba(245,243,239,0.45)",
        }}>Quota di partecipazione</span>
        <span style={{
          fontFamily: HN, fontWeight: 900, fontSize: "28px",
          letterSpacing: "-0.02em", color: "#F5F3EF",
        }}>€ {price.toFixed(2).replace(".", ",")}</span>
      </div>

      {/* Fee row */}
      {fee > 0 && (
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: "8px" }}>
          <span style={{
            fontFamily: HN, fontSize: "9px", fontWeight: 700,
            letterSpacing: "0.3em", textTransform: "uppercase",
            color: "rgba(245,243,239,0.45)",
          }}>Commissione</span>
          <span style={{
            fontFamily: HN, fontWeight: 700, fontSize: "16px",
            color: "rgba(245,243,239,0.65)",
          }}>+ € {fee.toFixed(2).replace(".", ",")}</span>
        </div>
      )}

      {/* Total when quantity > 1 */}
      {quantity > 1 && (
        <div style={{
          display: "flex", alignItems: "baseline", justifyContent: "space-between",
          marginTop: "12px", paddingTop: "12px",
          borderTop: "1px solid rgba(245,243,239,0.08)",
        }}>
          <span style={{
            fontFamily: HN, fontSize: "9px", fontWeight: 700,
            letterSpacing: "0.3em", textTransform: "uppercase",
            color: "rgba(245,243,239,0.45)",
          }}>Totale ({quantity} persone)</span>
          <span style={{
            fontFamily: HN, fontWeight: 900, fontSize: "22px",
            letterSpacing: "-0.02em", color: ACC,
          }}>€ {total.toFixed(2).replace(".", ",")}</span>
        </div>
      )}

      {/* Membership note */}
      {membershipIncluded && membershipPrice != null && (
        <p style={{
          fontFamily: CH, fontSize: "12px", fontStyle: "italic",
          color: "rgba(245,243,239,0.35)", margin: "10px 0 0",
        }}>
          Tessera associativa annuale (€ {membershipPrice}/anno) inclusa nel prezzo.
        </p>
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
