"use client"

import { useEffect, useState, Suspense } from "react"
import dynamic from "next/dynamic"
import { Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { getEventById } from "@/services/events"
import { EVENT_COMPONENTS, EVENT_TYPES } from "@/config/events-utils"
import StaticHeader from "@/components/pages/events/StaticHeader"
import { analytics } from "@/config/firebase"
import { logEvent } from "firebase/analytics"
import { getSetting } from "@/services/admin/settings"
import PaymentWarningModal from "@/components/popups/PaymentWarningModal"

/* -------- tiny placeholders -------- */

const Spinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-black">
    <Loader2 className="w-8 h-8 text-mcp-orange animate-spin" />
  </div>
)

const ErrorBanner = ({ msg }) => (
  <div className="min-h-screen bg-black">
    <div className="h-24" />
    <div className="container mx-auto px-4 pt-16">
      <Alert className="bg-mcp-orange/10 border-mcp-orange/20">
        <AlertDescription className="text-white text-center text-lg font-helvetica">
          {msg}
        </AlertDescription>
      </Alert>
    </div>
  </div>
)

/* -------- main wrapper -------- */

export function EventContent({ id }) {
  const [event, setEvent] = useState(null)
  const [settings, setSettings] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showInfo, setShowInfo] = useState(false)

  useEffect(() => {
    if (!id) {
      setError("ID evento non fornito")
      setLoading(false)
      return
    }

    const loadAll = async () => {
      setLoading(true)

      const ev = await getEventById(id)
      if (!ev.success || !ev.event) {
        setError(ev.error || "Evento non disponibile")
      } else {
        setEvent(ev.event)
        if (analytics) {
          logEvent(analytics, "page_event_view", {
            event_id: id,
            event_title: ev.event.title ?? "Untitled",
            event_type: ev.event.type ?? "unknown"
          })
        }
      }

      const [resPB, resIBAN, resInt] = await Promise.all([
        getSetting("payment_blocked"),
        getSetting("company_iban"),
        getSetting("company_intestatario"),
      ])

      setSettings({
        payment_blocked: !resPB.error && Boolean(resPB.data?.value),
        company_iban: resIBAN.error ? "" : String(resIBAN.data?.value ?? ""),
        company_intestatario: resInt.error ? "" : String(resInt.data?.value ?? "")
      })

      setLoading(false)
    }

    loadAll()
  }, [id])

  useEffect(() => {
    if (!loading && event && settings?.payment_blocked) {
      setShowInfo(true)
    }
  }, [loading, event, settings])

  if (loading) return <Spinner />
  if (error || !event || !settings) return <ErrorBanner msg={error || "Errore di caricamento"} />

  const Content = EVENT_COMPONENTS[event.type] ?? EVENT_COMPONENTS[EVENT_TYPES.STANDARD]

  return (
    <div className="min-h-screen bg-black">
      <div className="h-24" />
      <Suspense fallback={<Spinner />}>
        <StaticHeader event={event} />
        <Content id={id} event={event} settings={settings} />
      </Suspense>

      <PaymentWarningModal
        open={showInfo}
        onClose={() => setShowInfo(false)}
        price={event.price ?? 18}
        iban={settings.company_iban}
        intestatario={settings.company_intestatario}
      />
    </div>
  )
}