"use client"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ContactUs } from "@/components/pages/ContactUs"
import { LogoSection } from "@/components/pages/Logo"
import { NextEventSection } from "@/components/pages/NextEventSection"
import { AboutUs } from "@/components/pages/AboutUs"
import { getNextEvent } from "@/services/events"
import { useEffect, useState } from "react"
import { NewsletterFooter } from "@/components/pages/NewsLetterFooter"
import { AnimatedSectionDivider } from "@/components/AnimatedSectionDivider"

export default function LandingPage() {
  const [nextEvent, setNextEvent] = useState(null)
  const [hasNextEvent, setHasNextEvent] = useState(false)

  useEffect(() => {
    async function fetchNextEvent() {
      try {
        const response = await getNextEvent()
        if (response.success && response.event) {
          setNextEvent(response.event)
          setHasNextEvent(true)
        }
      } catch (error) {
        console.error("Error fetching next event:", error)
      }
    }
    fetchNextEvent()
  }, [])

  return (
    <div className="min-h-screen font-helvetica">
      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center">
        <LogoSection />
      </section>

      {/* Divider 1 - Orange */}
      <AnimatedSectionDivider color="ORANGE" />

      {/* Next Event Section */}
      {hasNextEvent && (
        <>
          <section className="py-24 relative">
            <div className="absolute inset-0 bg-gradient-to-b from-black/0 via-mcp-orange/5 to-black/0" />
            <NextEventSection event={nextEvent} />
          </section>

          {/* Divider 2 - Red */}
          <AnimatedSectionDivider color="RED" />
        </>
      )}

      {/* About Section */}
      <section id="about" className="relative py-24">
        <AboutUs />
      </section>

      {/* Divider 3 - Orange */}
      <AnimatedSectionDivider color="ORANGE" />

      {/* Join Us Section */}
      <section id="join" className="relative py-24">
        <div className="container mx-auto px-4 text-center">
          <h2 className="font-charter text-4xl font-bold mb-8 gradient-text">Join Our Community</h2>
          <p className="font-helvetica text-lg mb-8 text-gray-300 max-w-2xl mx-auto">
            Become a part of our movement and experience the power of music connection.
          </p>
          <Link href="/subscribe">
            <Button size="lg" className="font-atlantico bg-mcp-gradient hover:opacity-90 text-white border-0">
              Sign Up Now
            </Button>
          </Link>
        </div>
      </section>

      {/* Divider 4 - Red */}
      <AnimatedSectionDivider color="RED" />

      {/* Contact Section */}
      <section id="contact-section" className="relative py-24">
        <ContactUs />
      </section>

      {/* Newsletter Footer */}
      <NewsletterFooter />
    </div>
  )
}

