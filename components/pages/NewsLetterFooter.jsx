"use client"

import { useState, useEffect } from "react"
import { ArrowRight } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { sendNewsLetterRequest } from "@/services/newsLetter"
import { PolicyLinks } from "@/components/pages/PolicyLinks"

export function NewsletterFooter() {
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

  return (
    <div className="relative w-full">
      {/* Gradient background with increased transparency */}
      <div className="absolute inset-0 bg-mcp-gradient opacity-80"></div>

      {/* Content */}
      <div className="relative py-6 sm:py-8">
        <div className="container mx-auto px-4 max-w-6xl">
          {/* Center everything on mobile */}
          <div className="text-center mb-4 sm:mb-6">
            <div className="flex justify-center mb-2">
              <Image src="/secondaryLogo.png" alt="MCP Logo" width={65} height={60} className="h-auto" />
            </div>
            <p className="text-black text-xs sm:text-sm">
              Subscribe to our newsletter and stay updated with our news
            </p>
          </div>

          {/* Centered form with responsive width */}
          <form onSubmit={handleNewsletter} className="flex w-full max-w-md mx-auto gap-2 mb-6">
            <Input
              id="newsletter-email"
              type="email"
              placeholder="enter your email@email.com"
              value={emailNewsLetter}
              onChange={(e) => setEmailNewsLetter(e.target.value)}
              className="flex-1 bg-black border-none text-white placeholder:text-gray-500 h-12"
              required
              disabled={loading}
            />
<Button
  type="submit"
  className="bg-gradient-to-r from-[#f5f5dc] to-[#fff5e1] hover:opacity-90 text-black font-bold px-4 h-12 rounded-md transition-all duration-300 transform hover:scale-105"
  disabled={loading}
>
  {loading ? (
    <div className="h-5 w-5 animate-spin rounded-full border-2 border-black border-t-transparent" />
  ) : (
    <ArrowRight className="h-5 w-5" />
  )}
</Button>
          </form>

          {status.message && (
            <div className="w-full max-w-md mx-auto mb-4">
              <Alert
                className={`${status.type === "success" ? "bg-green-500 border-green-600" : "bg-red-500 border-red-600"}`}
              >
                <AlertDescription className="text-white text-sm">{status.message}</AlertDescription>
              </Alert>
            </div>
          )}

          {/* Copyright text */}
          <div className="text-center text-xs sm:text-sm text-black">
            <p className="py-3">&copy; {new Date().getFullYear()} Music Connecting People. All rights reserved.</p>

          </div>
        </div>
      </div>
    </div>
  )
}

