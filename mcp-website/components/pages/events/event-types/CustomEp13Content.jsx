"use client"

import { useState, useEffect, useMemo } from "react"
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
import { PURCHASE_TYPES } from "@/config/purchaseTypes"

const fadeInUp = { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.6 } }
const splitLines = txt => txt.replace(/\\n/g, "\n").split("\n").filter(l => l.trim())

// EP13: attivo se evento attivo e price definito (la membership può essere auto-gestita dal backend)
const isEventActive = event => Boolean(event?.active) && typeof event?.price === "number"

const isEventPast = event => {
  if (!event?.date) return false
  const [d, m, y] = event.date.split("-").map(Number)
  // evento considerato “passato” dal giorno successivo a mezzanotte
  const eventEnd = new Date(y, m - 1, d + 1)
  return new Date() >= eventEnd
}

export default function CustomEp13Content({ id, event, settings }) {
  const [quantity, setQuantity] = useState(1)
  const [participants, setParticipants] = useState([])
  const [modalOpen, setModalOpen] = useState(false)
  const [formComplete, setFormComplete] = useState(false)
  const [imageUrl, setImageUrl] = useState(null)
  const [error, setError] = useState(null)
  const [newsletterConsent, setNewsletterConsent] = useState(true)
  const [eventMeta, setEventMeta] = useState({ nonMembers: [] })

  const active = isEventActive(event)
  const past = isEventPast(event)

  const paymentBlocked = Boolean(settings?.payment_blocked)
  const iban = settings?.company_iban || ""
  const intestatario = settings?.company_intestatario || ""

  useEffect(() => {
    if (event?.image) getImageUrl("events", `${event.image}.jpg`).then(setImageUrl).catch(() => {})
  }, [event?.image])

  // Prezzo finale IDENTICO per tutti (members o non-members): event.price (+event.fee se presente).
  // L’eventuale tesseramento viene gestito dal backend senza cambiare il totale pagato dall’utente.
  const cart = useMemo(() => {
    const price = typeof event?.price === "number" ? event.price : 0
    const fee = typeof event?.fee === "number" ? event.fee : 0

    // Applica consenso newsletter a tutti i partecipanti, se spuntato
    const updatedParticipants = newsletterConsent
      ? participants.map(p => ({ ...p, newsletterConsent: true }))
      : participants

    return {
      eventId: event?.id,
      quantity,
      participants: updatedParticipants,
      price,
      fee,
      // membershipFee può non essere mostrata: il backend decide se applicare il tesseramento “incluso”
      membershipFee: event?.membershipFee,
      total: (price + fee) * quantity,
      eventMeta,
    }
  }, [quantity, participants, event, newsletterConsent, eventMeta])

  // Determina il tipo di acquisto da inviare al backend:
  // - onlyMembers=true  -> solo biglietto, backend verifica che siano membri
  // - onlyMembers=false -> backend decide automaticamente se includere tesseramento (EP12-like), ma prezzo resta price
  const purchaseType = event?.onlyMembers ? PURCHASE_TYPES.EVENT : PURCHASE_TYPES.EVENT_OR_EVENT_AND_MEMBERSHIP

  if (!event) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-mcp-orange" />
      </div>
    )
  }
  if (error) {
    return (
      <div className="min-h-screen bg-black">
        <div className="h-24" />
        <div className="container mx-auto px-4 pt-16">
          <Alert className="bg-mcp-orange/10 border-mcp-orange/20">
            <AlertDescription className="text-white text-center text-lg font-helvetica">
              {error}
            </AlertDescription>
          </Alert>
        </div>
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
            {/* Header prezzo + policy membership */}
            <div className="text-center mb-4">
              {active && !past ? (
                <>
                  <div className="flex items-baseline gap-2 justify-center flex-wrap">
                    <div className="font-atlantico text-4xl text-mcp-orange">{event.price}€</div>
                    {typeof event.fee === "number" && event.fee > 0 && (
                      <div className="text-sm text-white tracking-wide uppercase">+ {event.fee}€ Fee</div>
                    )}
                  </div>

                  {/* Messaggi diversi a seconda di onlyMembers */}
                  {event.onlyMembers ? (
                    <>
                      <div className="mt-2 flex items-center justify-center">
                        <Badge variant="success" className="uppercase tracking-wide">Solo Membri</Badge>
                      </div>
                      <div className="mt-1 text-gray-300 text-sm text-center">
                        Prima release riservata ai soli membri dell’associazione (verifica automatica al checkout).
                      </div>
                    </>
                  ) : (
                    <div className="font-helvetica text-sm text-gray-400 mt-2">
                      Se non sei membro, il tesseramento sarà incluso automaticamente senza costi extra rispetto al prezzo indicato.
                    </div>
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

            {/* Lineup */}
            {event.lineup?.length > 0 && (
              <div className="text-center mb-6">
                <h3 className="font-atlantico text-lg text-mcp-orange mb-1">LINEUP</h3>
                <ul className="space-y-1">
                  {event.lineup.map((a, i) => (
                    <li key={i} className="text-white font-helvetica text-sm">{a}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Note evento */}
            {active && event.note && (
              <div className="bg-mcp-orange/10 border border-mcp-orange/20 rounded-md p-4 mb-6 text-white font-helvetica text-sm">
                {splitLines(event.note).map((l, i) => (
                  <p key={i} className="mb-2 last:mb-0">{l}</p>
                ))}
              </div>
            )}

            {/* Se pagamento bloccato → info IBAN */}
            {paymentBlocked ? (
              <PaymentBlockedWarning price={event.price ?? 18} iban={iban} intestatario={intestatario} />
            ) : (
              <>
                {/* Past / Upcoming */}
                {past ? (
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
                    {/* Quantità e info partecipanti */}
                    <QuantitySelector
                      quantity={quantity}
                      setQuantity={formComplete ? () => {} : setQuantity}
                      disabled={formComplete}
                    />

                    {/* In EP13 mostriamo comunque il pannello informativo.
                        Se onlyMembers=true, il testo del pannello può ignorare membershipFee
                        perché il prezzo resta invariato. */}
                    { (
                      <ParticipantsInfoPanel
                       event={event}
                        quantity={quantity}
                        membershipFee={event.membershipFee}
                      />
                    )}

                    {formComplete && participants.length === quantity ? (
                      <>
                        <SelectParticipants participants={participants} />

                        <div className="mt-6">
                          <label className="flex items-start gap-2 text-sm text-gray-300">
                            <input
                              type="checkbox"
                              className="mt-1"
                              checked={newsletterConsent}
                              onChange={e => setNewsletterConsent(e.target.checked)}
                            />
                            <span>
                              Acconsento a ricevere comunicazioni promozionali da parte
                              dell’associazione Music Connecting People via email, come descritto nella nostra{" "}
                              <a href="/privacy" target="_blank" className="underline">informativa sulla privacy</a>.
                            </span>
                          </label>
                        </div>

                        {/* Checkout */}
                        <div className="mt-8">
                          {/* purchase_type:
                              - "event_only"        (solo membri; backend verifica i nominativi)
                              - "auto_membership"   (backend include il tesseramento se necessario)
                           */}
                          <PayPalSection
                            event={event}
                            cart={cart}
                            purchase_type={purchaseType}
                          />
                        </div>
                      </>
                    ) : (
                      <ProceedButton onClick={() => setModalOpen(true)} />
                    )}
                  </>
                )}
              </>
            )}
          </motion.div>
        </div>
      </div>

      {/* Modale partecipanti */}
      {!paymentBlocked && (
        <ParticipantsModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          quantity={quantity}
          event={event}
          eventMeta={eventMeta}
          onEventMetaChange={setEventMeta}
          onSubmit={(data) => {
            // Data può essere un array (retro-compat) o un oggetto { participants, eventMeta }
            if (Array.isArray(data)) {
              setParticipants(data)
              // se la modale non restituisce eventMeta, preserva lo stato attuale
              setEventMeta(prev => prev ?? { nonMembers: [] })
            } else if (data && Array.isArray(data.participants)) {
              setParticipants(data.participants)
              setEventMeta(data.eventMeta ?? { nonMembers: [] })
            } else {
              // fallback difensivo
              setEventMeta(prev => prev ?? { nonMembers: [] })
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