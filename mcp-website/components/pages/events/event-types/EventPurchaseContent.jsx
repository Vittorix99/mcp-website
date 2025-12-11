"use client"

import { useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { Loader2 } from "lucide-react"
import Link from "next/link"

import PaymentBlockedWarning from "@/components/warnings/PaymentBlockedWarning"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { getImageUrl } from "@/config/firebaseStorage"
import QuantitySelector from "@/components/pages/events/QuantitySelector"
import ParticipantsInfoPanel from "@/components/pages/events/ParticipantsInfoPanel"
import { PayPalSection } from "@/components/pages/events/PayPalSection"
import ParticipantsModal from "@/components/pages/events/modals/ParticipantsModal"
import EventImage from "@/components/pages/events/EventImage"
import { SelectParticipants } from "@/components/pages/events/SelectParticipants"
import { resolvePurchaseMode, PURCHASE_MODES, ensureMembershipFee } from "@/config/events-utils"

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6 },
}

const splitLines = (txt = "") =>
  String(txt)
    .replace(/\\n/g, "\n")
    .split("\n")
    .filter((line) => line.trim().length)

const isEventActive = (event) => Boolean(event?.active) && typeof event?.price === "number"

const isEventPast = (event) => {
  if (!event?.date) return false
  const [d, m, y] = event.date.split("-").map(Number)
  const eventEnd = new Date(y, m - 1, d + 1)
  return new Date() >= eventEnd
}

const MODE_BADGES = {
  [PURCHASE_MODES.PUBLIC]: null,
  [PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS]: { label: "Solo membri registrati", tone: "success" },
  [PURCHASE_MODES.ONLY_MEMBERS]: { label: "Membership inclusa", tone: "secondary" },
  [PURCHASE_MODES.ON_REQUEST]: { label: "On request", tone: "secondary" },
}

const MODE_COPY = {
  [PURCHASE_MODES.PUBLIC]: "Evento aperto a tutti i soci e alle nuove richieste di tesseramento.",
  [PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS]:
    "Accesso riservato ai membri già registrati. Inserisci i dati con cui risulti tesserato.",
  [PURCHASE_MODES.ONLY_MEMBERS]:
    "Se un partecipante non è ancora membro, il backend attiverà automaticamente la tessera associativa.",
  [PURCHASE_MODES.ON_REQUEST]:
    "Questo evento richiede l'approvazione dello staff. Invia la tua richiesta per ricevere istruzioni.",
}

export default function EventPurchaseContent({ id, event, settings }) {
  const [quantity, setQuantity] = useState(1)
  const [participants, setParticipants] = useState([])
  const [modalOpen, setModalOpen] = useState(false)
  const [formComplete, setFormComplete] = useState(false)
  const [imageUrl, setImageUrl] = useState(null)
  const [newsletterConsent, setNewsletterConsent] = useState(true)
  const [eventMeta, setEventMeta] = useState({ nonMembers: [] })

  const purchaseMode = resolvePurchaseMode(event)
  const active = isEventActive(event)
  const past = isEventPast(event)
  const paymentBlocked = Boolean(settings?.payment_blocked)
  const iban = settings?.company_iban || ""
  const intestatario = settings?.company_intestatario || ""

  const requiresExistingMembership = purchaseMode === PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS
  const membershipIncluded = purchaseMode === PURCHASE_MODES.ONLY_MEMBERS
  const isOnRequest = purchaseMode === PURCHASE_MODES.ON_REQUEST

  useEffect(() => {
    if (event?.image) {
      getImageUrl("events", `${event.image}.jpg`).then(setImageUrl).catch(() => {})
    }
  }, [event?.image])

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
      membershipFee: ensureMembershipFee(event?.membershipFee),
      total: (price + fee) * quantity,
      eventMeta,
      purchaseMode,
    }
  }, [quantity, participants, event, newsletterConsent, eventMeta, purchaseMode])

  if (!event) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-mcp-orange" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-black mb-10">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
          <EventImage imageUrl={imageUrl} title={event.title} />

          <motion.div
            initial="initial"
            animate="animate"
            variants={fadeInUp}
            className="bg-black/80 backdrop-blur-md border border-mcp-orange/20 p-6 rounded-lg"
          >
            <div className="text-center mb-4 space-y-3">
              {active && !past ? (
                <>
                  <div className="flex items-baseline gap-2 justify-center flex-wrap">
                    <div className="font-atlantico text-4xl text-mcp-orange">
                      {typeof event.price === "number" ? `${event.price}€` : "--"}
                    </div>
                    {typeof event.fee === "number" && event.fee > 0 && (
                      <div className="text-sm text-white tracking-wide uppercase">+ {event.fee}€ Fee</div>
                    )}
                  </div>
                  {!!MODE_BADGES[purchaseMode] && (
                    <div className="flex justify-center">
                      <Badge variant={MODE_BADGES[purchaseMode].tone} className="uppercase tracking-wide">
                        {MODE_BADGES[purchaseMode].label}
                      </Badge>
                    </div>
                  )}
                  <p className="font-helvetica text-sm text-gray-400">
                    {MODE_COPY[purchaseMode] || MODE_COPY[PURCHASE_MODES.PUBLIC]}
                  </p>
                  {membershipIncluded && (
                    <p className="text-xs uppercase tracking-wide text-mcp-orange">
                      Se non hai già la tessera MCP, l’acquisto la include insieme al resto dell’ordine.
                    </p>
                  )}
                </>
              ) : (
                <div className="text-gray-400 italic">Prezzo non disponibile</div>
              )}

              <a
                href="https://drive.google.com/file/d/1IABjzNtUon0Ti32iJMxQdSPkLa4GcdKN/view"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-white/80 underline hover:text-white transition"
              >
                Visualizza lo statuto dell’associazione
              </a>
            </div>

            {event.lineup?.length > 0 && (
              <div className="text-center mb-6">
                <h3 className="font-atlantico text-lg text-mcp-orange mb-1">LINEUP</h3>
                <ul className="space-y-1">
                  {event.lineup.map((artist, idx) => (
                    <li key={idx} className="text-white font-helvetica text-sm">
                      {artist}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {active && event.note && (
              <div className="bg-mcp-orange/10 border border-mcp-orange/20 rounded-md p-4 mb-6 text-white font-helvetica text-sm">
                {splitLines(event.note).map((line, idx) => (
                  <p key={idx} className="mb-2 last:mb-0">
                    {line}
                  </p>
                ))}
              </div>
            )}

            {isOnRequest ? (
              <Alert className="bg-mcp-orange/10 border-mcp-orange/40 text-white">
                <AlertDescription className="space-y-3 text-center">
                  <p className="uppercase tracking-wide text-sm text-mcp-orange">
                    Evento accessibile su richiesta agli organizzatori
                  </p>
                  <p>
                    Invia una mail a{" "}
                    <a href="mailto:info@musicconnectingpeople.org" className="underline">
                      info@musicconnectingpeople.org
                    </a>{" "}
                    indicando nome, cognome e motivo dell’interesse. Il team ti ricontatterà con tutti i dettagli.
                  </p>
                </AlertDescription>
              </Alert>
            ) : paymentBlocked ? (
              <PaymentBlockedWarning price={event.price ?? 18} iban={iban} intestatario={intestatario} />
            ) : past ? (
              <div className="text-center mt-10">
                <div className="italic text-white mb-4">Evento concluso</div>
                {event.photosReady && (
                  <Link
                    href={`/events-foto/${event.id}`}
                    className="bg-white text-black px-6 py-2 rounded-md font-semibold hover:bg-gray-200"
                  >
                    Guarda le foto
                  </Link>
                )}
              </div>
            ) : !active ? (
              <div className="flex justify-center mt-12">
                <div className="bg-white text-black px-4 py-3 rounded-md text-sm">Evento non ancora disponibile</div>
              </div>
            ) : (
              <>
                <QuantitySelector
                  quantity={quantity}
                  setQuantity={formComplete ? () => {} : setQuantity}
                  disabled={formComplete}
                />

                <ParticipantsInfoPanel event={{ ...event, membershipFee: ensureMembershipFee(event?.membershipFee) }} quantity={quantity} purchaseMode={purchaseMode} />

                {formComplete && participants.length === quantity ? (
                  <>
                    <SelectParticipants participants={participants} />

                    <div className="mt-6">
                      <label className="flex items-start gap-2 text-sm text-gray-300">
                        <input
                          type="checkbox"
                          className="mt-1"
                          checked={newsletterConsent}
                          onChange={(e) => setNewsletterConsent(e.target.checked)}
                        />
                        <span>
                          Acconsento a ricevere comunicazioni promozionali via email, come descritto nella nostra{" "}
                          <a href="/privacy" target="_blank" className="underline">
                            informativa sulla privacy
                          </a>
                          .
                        </span>
                      </label>
                    </div>

                    <div className="mt-8">
                      <PayPalSection event={event} cart={cart} purchaseMode={purchaseMode} />
                    </div>
                  </>
                ) : (
                  <ProceedButton onClick={() => setModalOpen(true)} />
                )}
              </>
            )}
          </motion.div>
        </div>
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

function ProceedButton({ onClick, disabled = false }) {
  return (
    <div className="text-center mt-6">
      <button
        onClick={onClick}
        disabled={disabled}
        className={`px-12 py-3 rounded-md font-helvetica text-base font-semibold shadow transition-colors ${
          disabled ? "bg-gray-600 text-white cursor-not-allowed" : "bg-white text-black hover:bg-gray-100"
        }`}
      >
        Procedi con i dati dei partecipanti
      </button>
    </div>
  )
}
