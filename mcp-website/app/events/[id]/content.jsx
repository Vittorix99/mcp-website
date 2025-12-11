"use client"

import { useEffect, useState, Suspense } from "react"
import { Loader2 } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { EVENT_CONTENT_COMPONENT, resolvePurchaseMode } from "@/config/events-utils"
import StaticHeader from "@/components/pages/events/StaticHeader"
import { analytics } from "@/config/firebase"
import { logEvent } from "firebase/analytics"
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

export function EventContent({ id, event, settings, error }) {
  const [showInfo, setShowInfo] = useState(Boolean(settings?.payment_blocked))

  useEffect(() => {
    if (event && analytics) {
      logEvent(analytics, "page_event_view", {
        event_id: id,
        event_title: event.title ?? "Untitled",
        purchase_mode: resolvePurchaseMode(event),
      })
    }
  }, [id, event])

  useEffect(() => {
    setShowInfo(Boolean(settings?.payment_blocked))
  }, [settings?.payment_blocked])

  if (error) return <ErrorBanner msg={error} />
  if (!event || !settings) return <ErrorBanner msg="Evento non disponibile" />

  const Content = EVENT_CONTENT_COMPONENT

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
