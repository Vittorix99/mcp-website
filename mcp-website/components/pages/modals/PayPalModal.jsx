"use client"

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { CheckCircle2 } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"

const getSuccessMessage = (type) => {
  switch (type) {
    case "membership":
      return "Grazie per esserti unito alla nostra associazione. Riceverai presto la tessera via mail.";
    case "event":
      return "Grazie per il tuo acquisto. Controlla la tua email per il biglietto.";
    case "event_and_membership":
      return "Grazie! Riceverai sia il biglietto che la tessera dell'associazione via mail.";
    default:
      return "Pagamento completato. Controlla la tua email.";
  }
}

export function PaymentSuccessDialog({ open, onOpenChange, purchaseType }) {
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
                  {getSuccessMessage(purchaseType)}
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