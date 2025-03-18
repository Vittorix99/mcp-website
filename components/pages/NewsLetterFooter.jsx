"use client"

import { useState, useEffect } from "react"
import { ArrowRight } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { sendNewsLetterRequest } from "@/services/newsLetter"

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
      <div className="relative py-4 sm:py-6">
        <div className="container mx-auto px-4 max-w-6xl">
          {/* Center everything on mobile */}
          <div className="text-center mb-3">
            <div className="flex justify-center mb-1">
              <Image src="/secondaryLogo.png" alt="MCP Logo" width={65} height={60} className="h-auto" />
            </div>
            <p className="font-helvetica text-black text-xs sm:text-sm">
              Subscribe to our newsletter and stay updated with our news
            </p>
          </div>

          {/* Centered form with responsive width */}
          <form onSubmit={handleNewsletter} className="flex w-full max-w-md mx-auto gap-2 mb-3">
            <Input
              id="newsletter-email"
              type="email"
              placeholder="enter your email@email.com"
              value={emailNewsLetter}
              onChange={(e) => setEmailNewsLetter(e.target.value)}
              className="font-helvetica flex-1 bg-black border-none text-white placeholder:text-gray-500 h-10"
              required
              disabled={loading}
            />
            <Button
              type="submit"
              className="bg-gradient-to-r from-[#f5f5dc] to-[#fff5e1] hover:opacity-90 text-black font-helvetica font-light px-4 h-10 rounded-md transition-all duration-300 transform hover:scale-105"
              disabled={loading}
            >
              {loading ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-black border-t-transparent" />
              ) : (
                <ArrowRight className="h-4 w-4" />
              )}
            </Button>
          </form>

          {status.message && (
            <div className="w-full max-w-md mx-auto mb-2">
              <Alert
                className={`${status.type === "success" ? "bg-green-500 border-green-600" : "bg-red-500 border-red-600"}`}
              >
                <AlertDescription className="font-helvetica text-white text-xs">{status.message}</AlertDescription>
              </Alert>
            </div>
          )}

          {/* Copyright text */}
          <div className="font-helvetica text-center text-xs text-black font-charter py-2">
            <p>&copy; {new Date().getFullYear()} Music Connecting People. All rights reserved.</p>

          </div>
        </div>
      </div>
    </div>
  )
}

