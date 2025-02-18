import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { CheckCircle2 } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"

export function PaymentSuccessDialog({ open, onOpenChange }) {
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
                  <span className="text-2xl font-bold gradient-text">Payment Successful!</span>
                </DialogTitle>
                <DialogDescription className="text-center text-gray-300">
                  Thank you for your purchase. Please check your email for your tickets.
                </DialogDescription>
              </DialogHeader>
              <div className="mt-6 flex justify-center">
                <Button
                  onClick={() => onOpenChange(false)}
                  className="bg-mcp-gradient hover:opacity-90 text-white font-bold py-2 px-4 rounded-md transition-all duration-300 transform hover:scale-105"
                >
                  Close
                </Button>
              </div>
            </motion.div>
          </DialogContent>
        </Dialog>
      )}
    </AnimatePresence>
  )
}

