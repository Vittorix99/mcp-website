"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { sendContactRequest } from "@/services/contactService"
import { CustomToast } from "@/components/CustomToast"
import { SectionTitle } from "@/components/ui/section-title"

export function ContactUs() {
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [message, setMessage] = useState("")
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        setToast(null)
      }, 5000)
      return () => clearTimeout(timer)
    }
  }, [toast])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await sendContactRequest({ name, email, message })
      setToast({ message: "Your message has been sent successfully!", type: "success" })
      setName("")
      setEmail("")
      setMessage("")
    } catch (error) {
      console.error("Error:", error.message)
      setToast({ message: error.message || "Failed to send message. Please try again.", type: "error" })
    } finally {
      setIsSubmitting(false)
    }
  }

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  }

  return (
    <div className="max-w-md mx-auto px-4 sm:px-0">
      <div className="contact-card bg-black/60 backdrop-blur-md rounded-2xl border border-white/10 shadow-2xl px-4 sm:px-6 py-6">
        <SectionTitle as="h1" className="mt-2 py-2 md:mt-4 text-3xl md:text-5xl text-center">
          Contact Us
        </SectionTitle>

        <motion.form
          onSubmit={handleSubmit}
          className="space-y-4 md:space-y-6"
          initial="initial"
          animate="animate"
          variants={fadeInUp}
        >
          <div>
            <Label htmlFor="contact-name" className="text-gray-300 mb-1 md:mb-2 block text-sm md:text-base">
              Name
            </Label>
            <Input
              id="contact-name"
              type="text"
              required
              className="bg-black/30 border border-white/15 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300 h-9 md:h-10 text-sm md:text-base"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
            />
          </div>
          <div>
            <Label htmlFor="contact-email" className="text-gray-300 mb-1 md:mb-2 block text-sm md:text-base">
              Email
            </Label>
            <Input
              id="contact-email"
              type="email"
              required
              className="bg-black/30 border border-white/15 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300 h-9 md:h-10 text-sm md:text-base"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
            />
          </div>
          <div>
            <Label htmlFor="contact-message" className="text-gray-300 mb-1 md:mb-2 block text-sm md:text-base">
              Message
            </Label>
            <Textarea
              id="contact-message"
              required
              className="bg-black/30 border border-white/15 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300 text-sm md:text-base min-h-[100px] md:min-h-[120px]"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Your message here..."
            />
          </div>
          <Button
            type="submit"
            className="w-full bg-mcp-gradient hover:opacity-90 text-white py-2 md:py-3 rounded-full transition-all duration-300 transform hover:scale-[1.02] text-sm md:text-base h-9 md:h-10 mt-2"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Sending..." : "Send Message"}
          </Button>
        </motion.form>

        <div className="h-4 md:h-6"></div>

        <AnimatePresence>
          {toast && <CustomToast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </AnimatePresence>
      </div>
    </div>
  )
}
