"use client"

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { CheckCircle2 } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { PURCHASE_MODES } from "@/config/events-utils"

const getSuccessMessage = (mode) => {
  switch (mode) {
    case PURCHASE_MODES.ONLY_ALREADY_REGISTERED_MEMBERS:
      return "Grazie! Riceverai a breve il biglietto via email all'indirizzo associato al tuo tesseramento."
    case PURCHASE_MODES.ONLY_MEMBERS:
      return "Grazie! Riceverai sia il biglietto che la tessera (se necessaria) via email."
    case PURCHASE_MODES.ON_REQUEST:
      return "Grazie! La tua richiesta è stata inoltrata al team."
    default:
      return "Pagamento completato. Controlla la tua email per il biglietto."
  }
}

export function PaymentSuccessDialog({ open, onOpenChange, purchaseMode }) {
  const fadeIn = {
    initial: { opacity: 0, scale: 0.9 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.9 },
    transition: { duration: 0.3 },
  }

  return (
    <AnimatePresence>
      {open && (
        <Dialog open={open} onOpenChange={onOpenChange}>
          <DialogContent className="bg-black border border-mcp-orange/50 sm:max-w-[425px] z-[9999]">
            <motion.div initial="initial" animate="animate" exit="exit" variants={fadeIn}>
              <DialogHeader className="space-y-6">
                <DialogTitle className="text-center flex flex-col items-center gap-4">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", stiffness: 260, damping: 20 }}
                  >
                    <CheckCircle2 className="h-16 w-16 text-green-500" />
                  </motion.div>
                  <span className="text-2xl font-light gradient-text tracking-wider md:tracking-normal">
                    Pagamento completato
                  </span>
                </DialogTitle>
              <DialogDescription className="text-center text-gray-300 font-light">
                  {getSuccessMessage(purchaseMode)}
                </DialogDescription>
              </DialogHeader>
              <div className="mt-6 flex justify-center">
                <Button
                  onClick={() => onOpenChange(false)}
                  className="bg-mcp-gradient hover:opacity-90 text-white font-light py-2 px-4 rounded-md transition-all duration-300 transform hover:scale-105"
                >
                  Chiudi
                </Button>
              </div>
            </motion.div>
          </DialogContent>
        </Dialog>
      )}
    </AnimatePresence>
  )
}
