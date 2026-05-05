"use client"

import { initialOptions } from "@/config/paypal"
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js"
import { useMemo, useState } from "react"
import { createOrder, onApprove } from "@/services/paypal"
import { toast } from "sonner"
import { PaymentSuccessDialog } from "@/components/pages/modals/PayPalModal"
import { Loader2, AlertCircle } from "lucide-react"
import { analytics } from "@/config/firebase"
import { logEvent } from "firebase/analytics"
import { resolvePurchaseMode } from "@/config/events-utils"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

export function PayPalSection({ event, cart, purchaseMode, disabled = false }) {
  const [showSuccess, setShowSuccess] = useState(false)
  const [isProcessing, setProcessing] = useState(false)
  const [orderError, setOrderError] = useState(null)
  const [locked, setLocked] = useState(false)

  const effectiveMode = useMemo(() => purchaseMode || resolvePurchaseMode(event), [purchaseMode, event])
  const extractErrorMessage = (payload, fallback) =>
    Array.isArray(payload?.messages) && payload.messages.length
      ? payload.messages.join(" ")
      : payload?.message || payload?.error || fallback

  const handleCreateOrder = async () => {
    setProcessing(true)
    setOrderError(null)

    if (analytics) {
      logEvent(analytics, "start_payment", {
        method: "unknown",
        event_id: event?.id || "unknown",
        total: cart?.total || 0,
        source: "create_order",
        purchase_mode: effectiveMode,
      })
    }

    try {
      const order = await createOrder({ cart })

      if (order?.error) {
        const message = extractErrorMessage(order, "Errore nella creazione dell'ordine.")
        setOrderError(message)
        toast.error(message)
        throw new Error(message)
      }

      const orderId = order?.id || order?.orderId || order?.result?.id || order?.data?.id
      if (orderId && typeof orderId === "string") {
        return orderId
      }

      const msg = "Risposta inattesa dal server: ID ordine mancante."
      setOrderError(msg)
      toast.error(msg)
      throw new Error(msg)
    } catch (err) {
      console.error("Order creation failed:", err)
      const message = err?.message || "Errore sconosciuto durante la creazione dell'ordine."
      setOrderError(message)
      toast.error(message)
      throw err
    } finally {
      setProcessing(false)
    }
  }

  const handleApprove = async (data, actions) => {
    setProcessing(true)
    try {
      const res = await onApprove(data.orderID)

      if (res?.purchase_id) {
        if (analytics) {
          logEvent(analytics, "payment_successful", {
            method: res.payment_method || data?.fundingSource || "unknown",
            purchase_id: res.purchase_id,
            event_id: event?.id || "unknown",
            total: cart?.total || 0,
            purchase_mode: effectiveMode,
          })
        }
        setShowSuccess(true)
        setLocked(true)
        return
      }

      if (res?.error) {
        const message = extractErrorMessage(res, "Pagamento non completato.")
        toast.error(message)
        if (analytics) {
          logEvent(analytics, "payment_failed", {
            method: data?.fundingSource || "unknown",
            reason: res?.error,
            event_id: event?.id || "unknown",
            total: cart?.total || 0,
            purchase_mode: effectiveMode,
          })
        }
        if (res?.error === "payment_not_completed" && actions?.restart) actions.restart()
        return
      }

      if (res?.details?.[0]) {
        if (analytics) {
          logEvent(analytics, "payment_failed", {
            method: data?.fundingSource || "unknown",
            reason: res.details[0].issue || "unknown",
            event_id: event?.id || "unknown",
            total: cart?.total || 0,
            purchase_mode: effectiveMode,
          })
        }
        toast.error(res.details[0].description || "Errore durante il pagamento.")
        if (res.details[0].issue === "INSTRUMENT_DECLINED" && actions?.restart) actions.restart()
        return
      }

      toast.error("Pagamento non confermato. Riprova.")
    } catch (err) {
      console.error(err)
      toast.error("Si è verificato un errore durante il pagamento. Riprova.")
    } finally {
      setProcessing(false)
    }
  }

  const totalLabel = typeof cart?.total === "number" && !isNaN(cart.total) ? `${cart.total.toFixed(2)}€` : "0.00€"

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "22px" }}>
      <div
        style={{
          borderTop: "1px solid rgba(245,243,239,0.08)",
          borderBottom: "1px solid rgba(245,243,239,0.08)",
          padding: "16px 0",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          gap: "20px",
        }}
      >
        <span
          style={{
            fontFamily: HN,
            fontSize: "8px",
            fontWeight: 700,
            letterSpacing: "0.35em",
            textTransform: "uppercase",
            color: ACC,
          }}
        >
          Totale
        </span>
        <span
          style={{
            fontFamily: HN,
            fontSize: "26px",
            fontWeight: 900,
            letterSpacing: "-0.02em",
            color: "#F5F3EF",
          }}
        >
          {totalLabel}
        </span>
      </div>

      <PayPalScriptProvider options={initialOptions}>
        {isProcessing && (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "16px 0", color: "rgba(245,243,239,0.55)" }}>
            <Loader2 style={{ width: 20, height: 20, color: ACC }} className="animate-spin" />
            <span style={{ marginLeft: 10, fontFamily: HN, fontSize: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
              Elaborazione...
            </span>
          </div>
        )}

        {orderError && (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 14, border: "1px solid rgba(209,0,0,0.35)", color: "#ffb6b6" }}>
            <AlertCircle style={{ width: 18, height: 18, marginRight: 8 }} />
            <span>{orderError}</span>
          </div>
        )}

        <PayPalButtons
          style={{ shape: "rect", layout: "vertical", color: "blue", label: "pay" }}
          createOrder={handleCreateOrder}
          onApprove={handleApprove}
          onClick={(data, actions) => {
            if (analytics) {
              logEvent(analytics, "start_payment", {
                method: data?.fundingSource || "unknown",
                event_id: event?.id || "unknown",
                total: cart?.total || 0,
                source: "paypal_button",
                purchase_mode: effectiveMode,
              })
            }
            return actions.resolve()
          }}
          disabled={disabled || isProcessing || locked}
        />
      </PayPalScriptProvider>

      <p style={{ fontFamily: CH, fontSize: "13px", lineHeight: 1.6, color: "rgba(245,243,239,0.38)", textAlign: "center", margin: 0 }}>
        Procedendo con il pagamento, accetti i nostri&nbsp;
        <a
          href="https://www.iubenda.com/termini-e-condizioni/78147975"
          style={{ color: ACC, textDecoration: "none", borderBottom: `1px solid ${ACC}` }}
        >
          Termini e Condizioni
        </a>
      </p>

      <PaymentSuccessDialog open={showSuccess} onOpenChange={setShowSuccess} purchaseMode={effectiveMode} />
    </div>
  )
}
