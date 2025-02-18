"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { sendNewsLetterRequest } from "@/services/newsLetter"

export function Newsletter() {
  const [emailNewsLetter, setEmailNewsLetter] = useState("")
  const [status, setStatus] = useState({ type: "", message: "" })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (status.type === "success") {
      const timer = setTimeout(() => {
        setStatus({ type: "", message: "" })
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [status.type])

  const handleNewsletter = async (e) => {
    e.preventDefault()
    setLoading(true)
    setStatus({ type: "", message: "" })

    try {
      const { success, message } = await sendNewsLetterRequest({ email: emailNewsLetter })

      if (success) {
        setStatus({
          type: "success",
          message: "Thanks for subscribing to our newsletter",
        })
        setEmailNewsLetter("")
      } else {
        setStatus({
          type: "error",
          message: message,
        })
      }
    } catch (error) {
      setStatus({
        type: "error",
        message: error.message || "An error occurred during subscription",
      })
    } finally {
      setLoading(false)
    }
  }

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  return (
    <div className="container mx-auto px-4">
      <div className="max-w-2xl mx-auto text-center">
        <motion.h2
          className="text-4xl font-bold mb-8 gradient-text"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          Stay Connected
        </motion.h2>
        <motion.p className="text-lg mb-8 text-gray-300" initial="initial" animate="animate" variants={fadeInUp}>
          Subscribe to our newsletter for exclusive updates and event announcements.
        </motion.p>

        <AnimatePresence mode="wait">
          {status.message && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <Alert
                className={`mb-6 ${
                  status.type === "success" ? "bg-green-500/10 border-green-500/20" : "bg-red-500/10 border-red-500/20"
                }`}
              >
                <AlertDescription className={`${status.type === "success" ? "text-green-400" : "text-red-400"}`}>
                  {status.message}
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.form
          onSubmit={handleNewsletter}
          className="flex gap-4 max-w-md mx-auto"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          <Input
            id="newsletter-email"
            type="email"
            placeholder="Enter your email"
            value={emailNewsLetter}
            onChange={(e) => setEmailNewsLetter(e.target.value)}
            className="flex-1 bg-black/30 border-mcp-orange/50 text-white placeholder:text-gray-500 focus:border-mcp-orange transition-colors duration-300"
            required
            disabled={loading}
          />
          <Button
            type="submit"
            className="bg-mcp-gradient hover:opacity-90 text-white px-3 py-2 rounded-md transition-all duration-300 transform hover:scale-105"
            disabled={loading}
          >
            {loading ? (
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <ArrowRight className="h-5 w-5" />
            )}
          </Button>
        </motion.form>
      </div>
    </div>
  )
}

