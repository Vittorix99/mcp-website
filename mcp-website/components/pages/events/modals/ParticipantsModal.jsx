"use client"

import { useState, useEffect, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Loader2, ChevronLeft, ChevronRight, X } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useCheckParticipants } from "@/hooks/useCheckParticipants"
import { useMediaQuery } from "@/hooks/useMediaQuery"
import { analytics } from "@/config/firebase"
import { logEvent } from "firebase/analytics"
import { EVENT_TYPES } from "@/config/events-utils"
import "@/app/style/modal.css"

export default function ParticipantsModal({ open, onOpenChange, quantity, event, eventMeta = { nonMembers: [] }, onEventMetaChange = () => {}, onSubmit }) {
  const empty = () => ({ name: "", surname: "", email: "", phone: "", birthdate: "" })
  const [fields, setFields] = useState([])
  const [current, setCurrent] = useState(0)
  const { checkParticipants, loading, errors: checkErrors } = useCheckParticipants()
  const isDesktop = useMediaQuery("(min-width: 768px)")

  // EP13 (onlyMembers=false): mostra disclaimer e consenso se alcuni non sono membri
  const [nonMembers, setNonMembers] = useState([])
  const [requireConsent, setRequireConsent] = useState(false)
  const [consentChecked, setConsentChecked] = useState(false)

  const disclaimerRef = useRef(null)
  const blockClose = requireConsent && !consentChecked
  const fieldsLocked = requireConsent === true

  useEffect(() => {
    if (open) {
      setRequireConsent(false)
      setConsentChecked(false)
      setNonMembers([])
      setFields(Array.from({ length: quantity || 0 }, empty))
      setCurrent(0)
      onEventMetaChange({ ...(eventMeta || {}), nonMembers: [] })
    }
  }, [quantity, open])

  const updateField = (key, value) => {
    setFields((prev) => {
      const updated = [...prev]
      updated[current] = { ...updated[current], [key]: value }
      return updated
    })
  }

  const handleBirthdateChange = (raw) => {
    const cleaned = raw.replace(/\D/g, "")
    let formatted = cleaned
    if (cleaned.length > 4) {
      formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2, 4)}-${cleaned.slice(4, 8)}`
    } else if (cleaned.length > 2) {
      formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2)}`
    }
    updateField("birthdate", formatted)
  }

  const validateField = (p = {}) => ({
    name: (p.name || "").trim().length < 2,
    surname: (p.surname || "").trim().length < 2,
    email: !/\S+@\S+\.\S+/.test(p.email || ""),
    phone: (p.phone || "").trim().length < 8,
    birthdate: !/^\d{2}-\d{2}-\d{4}$/.test(p.birthdate || ""),
  })

  const isCurrentValid = () => {
    const validation = validateField(fields[current] || {})
    return Object.values(validation).every((v) => !v)
  }

  const finalizeSubmit = () => {
    if (analytics) {
      logEvent(analytics, "add_participant", {
        event_id: event?.id || "unknown",
        quantity,
        step: "participant_modal",
      })
    }
    onSubmit({ participants: fields, eventMeta: eventMeta || { nonMembers: [] } })
    onOpenChange(false)
  }

  const handleConfirm = async () => {
    const allValid = fields.every((p) => Object.values(validateField(p)).every((v) => !v))
    if (!allValid) return

    // Se stiamo già mostrando il disclaimer di consenso per EP13
    if (requireConsent) {
      if (!consentChecked) return
      finalizeSubmit()
      return
    }

    // Esegue il check lato backend
    const result = await checkParticipants(event.id, fields)
    const valid = typeof result === "boolean" ? result : result?.valid
    if (!valid) return

    // EP13: onlyMembers=false -> non blocchiamo, ma se ci sono non-membri chiediamo consenso
    if ((event?.type || "").toLowerCase() === EVENT_TYPES.CUSTOM_EP13 && !event?.onlyMembers) {
      const nm = Array.isArray(result?.nonMembers) ? result.nonMembers : []
      if (nm.length > 0) {
        setNonMembers(nm)
        onEventMetaChange({ ...(eventMeta || {}), nonMembers: nm })
        setRequireConsent(true)
        setConsentChecked(false)

        // porta in vista il disclaimer prima di chiudere
        setTimeout(() => {
          if (disclaimerRef.current) {
            try { disclaimerRef.current.scrollIntoView({ behavior: "smooth", block: "start" }) } catch(_) {}
          }
        }, 0)

        onOpenChange(true)

        return
      }
    }

    finalizeSubmit()
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (current < quantity - 1) {
      if (isCurrentValid()) setCurrent((c) => c + 1)
    } else {
      handleConfirm()
    }
  }

  const renderFields = () => {
    const field = fields[current] || {}
    return (
      <div className="space-y-4">
        <AnimatePresence mode="wait">
          {checkErrors.length > 0 && (
            <motion.div
              key="check-errors"
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
            >
              <Alert className="bg-red-900/30 text-red-300 border-red-700">
                <AlertDescription className="text-sm space-y-1">
                  {checkErrors.map((msg, i) => (
                    <p key={`error-${i}`}>{msg}</p>
                  ))}
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
          {event.onlyMembers && checkErrors.length > 0 && (
            <motion.div
              key="only-members-error"
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
            >
              <Alert className="bg-yellow-900/30 text-yellow-300 border-yellow-700 mt-2">
                <AlertDescription className="text-sm">
                  Questo evento è riservato ai membri dell’associazione. I dati inseriti non risultano associati a un membro registrato.
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
          {requireConsent && nonMembers.length > 0 && (event?.type || "").toLowerCase() === "custom_ep13" && !event?.onlyMembers && (
            <motion.div
              key="ep13-nonmembers-disclaimer"
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              ref={disclaimerRef}
            >
              <Alert className="bg-yellow-900/30 text-yellow-300 border-yellow-700 mt-2">
                <AlertDescription className="text-sm space-y-2">
                  <p>
                    Alcuni partecipanti non risultano membri dell’associazione culturale. Procedendo con l’acquisto,
                    i partecipanti non membri accettano di diventare membri MCP ETS e accettano lo Statuto
                    dell’associazione.
                  </p>
                  <div className="text-xs opacity-80">
                    Non membri rilevati: {(eventMeta?.nonMembers?.length ? eventMeta.nonMembers : nonMembers).join(", ")}
                  </div>
                </AlertDescription>
              </Alert>
              <label className="mt-2 flex items-start gap-2 text-sm text-yellow-200">
                <input
                  type="checkbox"
                  className="mt-1 pointer-events-auto"
                  checked={!!consentChecked}
                  onChange={(e) => setConsentChecked(e.target.checked)}
                />
                <span>
                  Confermo che i partecipanti non membri accettano di diventare membri MCP ETS e di aderire allo Statuto
                  dell’associazione.
                </span>
              </label>
            </motion.div>
          )}
        </AnimatePresence>

        <div className={fieldsLocked ? "pointer-events-none opacity-70" : ""}>
          {[
            { key: "name", label: "Nome" },
            { key: "surname", label: "Cognome" },
            { key: "email", label: "Email", type: "email" },
            { key: "phone", label: "Telefono" },
            { key: "birthdate", label: "Data di nascita (gg-mm-aaaa)" },
          ].map(({ key, label, type }) => (
            <div key={key} className="space-y-2">
              <Label htmlFor={`${key}-${current}`} className="text-gray-300 text-sm font-medium">
                {label}
              </Label>
              <Input
                id={`${key}-${current}`}
                type={type || "text"}
                value={field[key] || ""}
                onChange={(e) => {
                  if (fieldsLocked) return
                  if (key === "birthdate") handleBirthdateChange(e.target.value)
                  else updateField(key, e.target.value)
                }}
                disabled={fieldsLocked}
                className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300 h-12 disabled:opacity-60 disabled:cursor-not-allowed"
                placeholder={label}
              />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const renderFooter = () => (
    <div className="flex justify-between items-center gap-3">
      <Button
        type="button"
        variant="ghost"
        onClick={() => setCurrent((c) => Math.max(0, c - 1))}
        disabled={current === 0 || fieldsLocked}
        className="flex-1 h-12"
      >
        <ChevronLeft className="w-4 h-4 mr-2" />
        Indietro
      </Button>

      {current < quantity - 1 ? (
        <Button type="submit" disabled={!isCurrentValid() || fieldsLocked} className="flex-1 h-12">
          Avanti <ChevronRight className="ml-2 w-4 h-4" />
        </Button>
      ) : (
        <Button type="submit" disabled={loading || !isCurrentValid() || (requireConsent && !consentChecked)} className="flex-1 h-12">
          {loading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> {requireConsent ? "Conferma" : "Verifica..."}
            </span>
          ) : (
            requireConsent ? (consentChecked ? "Conferma" : "Accetta e continua") : "Conferma"
          )}
        </Button>
      )}
    </div>
  )

  // Mobile full-screen overlay
  if (!isDesktop && open) {
    return (
      <div className="fixed inset-0 z-50 bg-black no-nav">
        <div className="flex flex-col h-full min-h-0">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-mcp-orange/20">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onOpenChange(false)}
                className="text-white hover:bg-mcp-orange/20"
                disabled={blockClose}
                title={blockClose ? "Conferma l'accettazione per continuare" : undefined}
              >
                <X className="w-5 h-5" />
              </Button>
              <div>
                <h2 className="text-lg font-helvetica font-bold gradient-text">
                  Partecipante {current + 1} di {quantity}
                </h2>
                <div className="flex gap-1 mt-1">
                  {Array.from({ length: quantity }).map((_, i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-colors ${
                        i <= current ? "bg-mcp-orange" : "bg-gray-700"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Content */}
          <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
            <div className="flex-1 min-h-0 p-4 overflow-y-auto pb-24">
              {renderFields()}
            </div>

            {/* Footer */}
            <div
              className="sticky bottom-0 p-4 border-t border-mcp-orange/20 bg-black/95 backdrop-blur supports-[backdrop-filter]:bg-black/60"
              style={{ paddingBottom: 'calc(env(safe-area-inset-bottom) + 1rem)' }}
            >
              {renderFooter()}
            </div>
          </form>
        </div>
      </div>
    )
  }

  // Desktop modal
  return (
    <Dialog open={open} onOpenChange={(v) => {
      if (requireConsent && !consentChecked && v === false) return
      onOpenChange(v)
    }}>
      <DialogContent
        className="sm:max-w-[480px] max-h-[90vh] bg-black border-mcp-orange/50 rounded-xl"
        onInteractOutside={(e) => { if (blockClose) e.preventDefault() }}
        onEscapeKeyDown={(e) => { if (blockClose) e.preventDefault() }}
      >
        <DialogHeader>
          <DialogTitle className="text-2xl font-helvetica font-bold gradient-text text-center">
            Partecipante {current + 1} di {quantity}
          </DialogTitle>
          <div className="flex gap-1 mt-3">
            {Array.from({ length: quantity }).map((_, i) => (
              <div
                key={i}
                className={`h-1 flex-1 rounded-full transition-colors ${
                  i <= current ? "bg-mcp-orange" : "bg-gray-700"
                }`}
              />
            ))}
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-6 min-h-0 max-h-[50vh] overflow-y-auto pr-2 pb-4">
          {renderFields()}
          {renderFooter()}
        </form>
      </DialogContent>
    </Dialog>
  )
}
