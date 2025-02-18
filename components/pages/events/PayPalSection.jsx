"use client"

import { initialOptions } from "@/config/paypal"
import { PayPalScriptProvider, PayPalButtons } from "@paypal/react-paypal-js"
import { useState } from "react"
import { motion } from "framer-motion"
import { createOrder, onApprove } from "@/services/paypal"
import { toast } from "sonner"
import { PaymentSuccessDialog } from "@/components/pages/modals/PayPalModal"
import { Loader2, AlertCircle } from "lucide-react"

export function PayPalSection({ event }) {
  const [showSuccessDialog, setShowSuccessDialog] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [orderError, setOrderError] = useState(null)

  const handleCreateOrder = async () => {
    setIsProcessing(true)
    setOrderError(null) // Reset error state
    try {
      const cart = {
        eventId: event.id,
        ticketPrice: event.price,
        quantity: 1,
      }

      const orderData = await createOrder(cart)

      if (orderData.id) {
        return orderData.id
      }

      throw new Error("Unable to create the order")
    } catch (error) {
      console.error("Error creating order:", error)
      setOrderError("Unable to create the order. Please try again later.")
      throw error
    } finally {
      setIsProcessing(false)
    }
  }

  const handleApprove = async (data, actions) => {
    setIsProcessing(true)
    try {
      const orderData = await onApprove(data.orderID)

      if (orderData.ticket_id) {
        setShowSuccessDialog(true)
        return
      } else if (orderData.details && orderData.details[0].issue === "INSTRUMENT_DECLINED") {
        toast.error("Your card was declined. Please try another card.")
        actions.restart()
        return
      } else if (orderData.details[0] && orderData.details[0].issue === "PERMISSION_DENIED") {
        toast.error("You don't have permission to make this payment.")
        return
      } else if (orderData.details[0]) {
        toast.error(orderData.details[0].description)
        return
      }

      // If we get here, something went wrong
      throw new Error("Error finalizing the payment")
    } catch (error) {
      console.error("Error capturing order:", error)
      toast.error("An error occurred during payment. Please try again later.")
    } finally {
      setIsProcessing(false)
    }
  }

  const fadeIn = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    transition: { duration: 0.5 },
  }

  return (
    <motion.div className="space-y-6" initial="initial" animate="animate" variants={fadeIn}>
      <PayPalScriptProvider options={initialOptions}>
        {isProcessing && (
          <div className="flex justify-center items-center py-4">
            <Loader2 className="w-6 h-6 text-mcp-orange animate-spin" />
            <span className="ml-2 text-gray-300">Processing payment...</span>
          </div>
        )}
        {orderError && (
          <div className="flex items-center justify-center p-4 bg-red-100 text-red-700 rounded-md">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>{orderError}</span>
          </div>
        )}
        <PayPalButtons
          style={{
            shape: "rect",
            layout: "vertical",
            color: "blue",
            label: "pay",
          }}
          createOrder={handleCreateOrder}
          onApprove={handleApprove}
          disabled={isProcessing}
        />
      </PayPalScriptProvider>

      <p className="text-sm text-gray-400 text-center">
        By proceeding with the payment, you agree to our{" "}
        <a href="/terms" className="text-mcp-orange hover:underline">
          Terms of Service
        </a>{" "}
        and{" "}
        <a href="/privacy" className="text-mcp-orange hover:underline">
          Privacy Policy
        </a>
        .
      </p>

      <PaymentSuccessDialog open={showSuccessDialog} onOpenChange={setShowSuccessDialog} />
    </motion.div>
  )
}

