"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { sendContactRequest } from "@/services/contactService"
import { CustomToast } from "@/components/pages/CustomToast"

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
    <div className="max-w-md mx-auto  bg-black/50 backdrop-blur-md rounded-lg shadow-lg">
      <motion.h2
        className="font-atlantico text-5xl md:text-5xl font-bold mb-8 gradient-text text-center "
        initial="initial"
        animate="animate"
        variants={fadeInUp}
      >
        Contact Us
      </motion.h2>
      <motion.form
        onSubmit={handleSubmit}
        className="space-y-6"
        initial="initial"
        animate="animate"
        variants={fadeInUp}
      >
        <div>
          <Label htmlFor="contact-name" className="text-gray-300 mb-2 block">
            Name
          </Label>
          <Input
            id="contact-name"
            type="text"
            required
            className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
          />
        </div>
        <div>
          <Label htmlFor="contact-email" className="text-gray-300 mb-2 block">
            Email
          </Label>
          <Input
            id="contact-email"
            type="email"
            required
            className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your@email.com"
          />
        </div>
        <div>
          <Label htmlFor="contact-message" className="text-gray-300 mb-2 block">
            Message
          </Label>
          <Textarea
            id="contact-message"
            required
            className="bg-black/30 border-mcp-orange/50 text-white placeholder-gray-500 focus:border-mcp-orange transition-colors duration-300"
            rows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Your message here..."
          />
        </div>
        <Button
          type="submit"
          className="w-full bg-mcp-gradient hover:opacity-90 text-white  py-3 rounded-md transition-all duration-300 transform hover:scale-105"
          disabled={isSubmitting}
        >
          {isSubmitting ? "Sending..." : "Send Message"}
        </Button>
      </motion.form>

      <AnimatePresence>
        {toast && <CustomToast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      </AnimatePresence>
    </div>
  )
}

