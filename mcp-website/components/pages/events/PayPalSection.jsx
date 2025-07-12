"use client"

import { initialOptions } from "@/config/paypal"
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js"
import { useState } from "react"
import { motion } from "framer-motion"
import { createOrder, onApprove } from "@/services/paypal"
import { toast } from "sonner"
import { PaymentSuccessDialog } from "@/components/pages/modals/PayPalModal"
import { Loader2, AlertCircle } from "lucide-react"
import { analytics } from "@/config/firebase"
import { logEvent } from "firebase/analytics"



export function PayPalSection({ event, cart, purchase_type="event",  disabled = false }) {
  const [showSuccess, setShowSuccess] = useState(false)
  const [isProcessing, setProcessing] = useState(false)
  const [orderError, setOrderError] = useState(null)

  /* ---------------- create ---------------- */
const handleCreateOrder = async () => {
  setProcessing(true)
  setOrderError(null)
  if (analytics) {
    logEvent(analytics, 'start_payment', {
      method: 'unknown',
      event_id: event?.id || 'unknown',
      total: cart?.total || 0,
      source: 'create_order'
    })
    console.log('[Analytics] start_payment tracciato da createOrder 🟡')
  }

  try {
    const payload = {
      purchase_type,
      cart
    }

    const order = await createOrder(payload)

    if (order?.error === "duplicate_participants") {
      const message = `I partecipanti risultano già tesserati`
      setOrderError(message)
      toast.error(message)
      return null
    }

    if (order?.id) return order.id

    setOrderError("Errore nella creazione dell'ordine.")
    toast.error("Errore nella creazione dell'ordine.")
    return null
  } catch (err) {
    console.error("Order creation failed:", err)
    const message = err?.message || "Errore sconosciuto durante la creazione dell'ordine."
    setOrderError(message)
    toast.error(message)
    return null
  } finally {
    setProcessing(false)
  }
}

  /* ---------------- capture ---------------- */
const handleApprove = async (data, actions) => {
  setProcessing(true)
  try {
    const res = await onApprove(data.orderID)

if (res.purchase_id) {
  // ✅ Firebase Analytics: pagamento effettuato
    console.log(data) 
    console.log(actions)
  if (analytics) {
    logEvent(analytics, 'payment_successful', {
      method:res.payment_method || 'unknown',
      purchase_id: res.purchase_id,
      event_id: event?.id || 'unknown',
      total: cart?.total || 0
    })
    console.log(`[Analytics] payment_successful con metodo: ${data?.fundingSource || 'unknown'}`)
  }

  setShowSuccess(true)
  disabled = true
  return
}

if (res?.details?.[0]) {
  // ❌ Firebase Analytics: pagamento fallito
  if (analytics) {
    console.log(data) 
    console.log(actions)
    logEvent(analytics, 'payment_failed', {
      method: data?.fundingSource || 'unknown',
      reason: res.details[0].issue || 'unknown',
      event_id: event?.id || 'unknown',
      total: cart?.total || 0
    })
    console.warn(`[Analytics] payment_failed — issue: ${res.details[0].issue}`)
  }

  toast.error(res.details[0].description || "Errore durante il pagamento.")
  if (res.details[0].issue === "INSTRUMENT_DECLINED") actions.restart()
  return
}
    // Fallback generico in caso di struttura imprevista
    toast.error("Pagamento completato ma non è stato possibile confermare l'acquisto.")
  } catch (err) {
    console.error(err)
    toast.error("Si è verificato un errore durante il pagamento. Riprova.")
  } finally {
    setProcessing(false)
  }
}
  /* ---------------- UI ---------------- */
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Totale */}
        <div className="bg-black/30 p-3 rounded-md">
          <div className="flex justify-between items-center">
            <span className="text-gray-300">Totale:</span>
            <span className="text-mcp-orange font-bold text-xl">
              {(typeof cart?.total === "number" && !isNaN(cart.total)) ? `${cart.total.toFixed(2)}€` : "0.00€"}
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
          disabled={disabled || isProcessing}
        />
      </PayPalScriptProvider>

      <p className="text-sm text-gray-400 text-center">
        Procedendo con il pagamento, accetti i nostri&nbsp;
        <a href="https://www.iubenda.com/termini-e-condizioni/78147975" className="text-mcp-orange hover:underline">Termini e Condizioni</a>
        
      </p>

<PaymentSuccessDialog
  open={showSuccess}
  onOpenChange={setShowSuccess}
  purchaseType={purchase_type}
/>    </motion.div>
  )
}