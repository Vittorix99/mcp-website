"use client"

import { useState, useEffect } from "react"
import { ArrowRight, Instagram, Youtube } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { sendNewsLetterRequest } from "@/services/newsLetter"
import { legalInfo, socialLinks, iubendaLinks } from "@/config/legal-info"
import { useMediaQuery } from "@/hooks/useMediaQuery"

export function Footer() {
  const [emailNewsLetter, setEmailNewsLetter] = useState("")
  const [status, setStatus] = useState({ type: "", message: "" })
  const [loading, setLoading] = useState(false)
  const isMobile = useMediaQuery("(max-width: 768px)")

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

  // Newsletter section - used in both mobile and desktop layouts
  const newsletterSection = (
    <div className={isMobile ? "w-full mb-2" : "w-1/4 pr-4"}>
      <div className="flex items-center gap-2 mb-2">
        <Image src="/secondaryLogo.png" alt="MCP Logo" width={50} height={50} className="h-auto" />
        <p className="font-helvetica text-xs">Stay updated with our news</p>
      </div>
      <form onSubmit={handleNewsletter} className="flex gap-2 mb-1">
        <Input
          type="email"
          placeholder="enter your email@email.com"
          value={emailNewsLetter}
          onChange={(e) => setEmailNewsLetter(e.target.value)}
          className="font-helvetica flex-1 bg-black text-white placeholder:text-gray-300 text-xs border-none h-8"
          required
          disabled={loading}
        />
        <Button
          type="submit"
          className="bg-white text-black h-8 px-2 hover:opacity-90 transition-all"
          disabled={loading}
        >
          {loading ? (
            <div className="h-3 w-3 animate-spin rounded-full border-2 border-black border-t-transparent" />
          ) : (
            <ArrowRight size={14} />
          )}
        </Button>
      </form>
      {status.message && (
        <Alert className={`py-0.5 ${status.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
          <AlertDescription className="font-helvetica text-white text-[10px]">{status.message}</AlertDescription>
        </Alert>
      )}
    </div>
  )

  // Social section - used in both mobile and desktop layouts
  const socialSection = (
    <div className={isMobile ? "w-1/3 text-center" : "w-1/4 text-center"}>
      <h3 className="font-charter text-[10px] md:text-sm font-bold uppercase mb-1">SOCIAL</h3>
      <div className="flex gap-2 md:gap-6 justify-center">
        <a href={socialLinks.instagram} target="_blank" rel="noopener noreferrer" className="hover:text-white">
          <Instagram size={isMobile ? 16 : 24} />
        </a>
        <a href={socialLinks.youtube} target="_blank" rel="noopener noreferrer" className="hover:text-white">
          <Youtube size={isMobile ? 16 : 24} />
        </a>
      </div>
    </div>
  )

  // Legal info section - used in both mobile and desktop layouts
  const legalInfoSection = (
    <div className={isMobile ? "w-1/3 px-1" : "w-1/4 pl-4"}>
      <h3 className="font-charter text-[10px] md:text-sm font-bold uppercase mb-1">INFORMATIVA LEGALE</h3>
      <div className="font-helvetica text-[8px] md:text-xs space-y-0 md:space-y-1">
        <p>{legalInfo.name}</p>
        <p>{legalInfo.address}</p>
        <p>P.IVA: {legalInfo.vat}</p>
        <p>CF: {legalInfo.fiscalCode}</p>
        <p>
          <a href={`mailto:${legalInfo.email}`} className="hover:text-white">
            {legalInfo.email}
          </a>
        </p>
      </div>
    </div>
  )

  // Links section - used in both mobile and desktop layouts
  const linksSection = (
    <div className={isMobile ? "w-1/3 pl-1" : "w-1/4 pl-4"}>
      <h3 className="font-charter text-[10px] md:text-sm font-bold uppercase mb-1">LINK UTILI</h3>
      <div className="font-helvetica text-[8px] md:text-xs space-y-0.5 md:space-y-2">
        <a
          href={iubendaLinks.privacyPolicy}
          target="_blank"
          rel="noopener noreferrer"
          className="block hover:text-white"
        >
          Privacy Policy
        </a>
        <a
          href={iubendaLinks.cookiePolicy}
          target="_blank"
          rel="noopener noreferrer"
          className="block hover:text-white"
        >
          Cookie Policy
        </a>
      </div>
    </div>
  )

  return (
    <footer className="bg-mcp-gradient text-black relative z-10">
      <div className="container mx-auto px-4 py-2 max-w-7xl">
        {isMobile ? (
          // Mobile layout: Newsletter in first row, then three columns below
          <div className="flex flex-col">
            {/* First row: Newsletter */}
            {newsletterSection}
            {/* Second row: Legal info, Social, and Links in three columns */}
            <div className="flex flex-row justify-between items-start">
              {legalInfoSection}
              {socialSection}
              {linksSection}
            </div>
          </div>
        ) : (
          // Desktop layout: All sections in one row
          <div className="flex flex-row justify-between items-start">
            {newsletterSection}
            {socialSection}
            {legalInfoSection}
            {linksSection}
          </div>
        )}
      </div>
    </footer>
  )
}
