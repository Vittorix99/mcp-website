"use client"

import { initialOptions } from "@/config/paypal"
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js"
import { useMemo, useState } from "react"
import { motion } from "framer-motion"
import { createOrder, onApprove } from "@/services/paypal"
import { toast } from "sonner"
import { PaymentSuccessDialog } from "@/components/pages/modals/PayPalModal"
import { Loader2, AlertCircle } from "lucide-react"
import { analytics } from "@/config/firebase"
import { logEvent } from "firebase/analytics"
import { resolvePurchaseMode } from "@/config/events-utils"

export function PayPalSection({ event, cart, purchaseMode, disabled = false }) {
  const [showSuccess, setShowSuccess] = useState(false)
  const [isProcessing, setProcessing] = useState(false)
  const [orderError, setOrderError] = useState(null)
  const [locked, setLocked] = useState(false)

  const effectiveMode = useMemo(() => purchaseMode || resolvePurchaseMode(event), [purchaseMode, event])

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
        const message = order?.message || order?.error || "Errore nella creazione dell'ordine."
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
        const message = res?.message || res?.error || "Pagamento non completato."
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

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }} className="space-y-6">
      <div className="bg-black/30 p-3 rounded-md">
        <div className="flex justify-between items-center">
          <span className="text-gray-300">Totale:</span>
          <span className="text-mcp-orange font-bold text-xl">
            {typeof cart?.total === "number" && !isNaN(cart.total) ? `${cart.total.toFixed(2)}€` : "0.00€"}
          </span>
        </div>
      </div>

      <PayPalScriptProvider options={initialOptions}>
        {isProcessing && (
          <div className="flex justify-center items-center py-4">
            <Loader2 className="w-6 h-6 text-mcp-orange animate-spin" />
            <span className="ml-2 text-gray-300">Elaborazione...</span>
          </div>
        )}

        {orderError && (
          <div className="flex items-center justify-center p-4 bg-red-900/50 text-red-300 rounded-md">
            <AlertCircle className="w-5 h-5 mr-2" />
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

      <p className="text-sm text-gray-400 text-center">
        Procedendo con il pagamento, accetti i nostri&nbsp;
        <a href="https://www.iubenda.com/termini-e-condizioni/78147975" className="text-mcp-orange hover:underline">
          Termini e Condizioni
        </a>
      </p>

      <PaymentSuccessDialog open={showSuccess} onOpenChange={setShowSuccess} purchaseMode={effectiveMode} />
    </motion.div>
  )
}
