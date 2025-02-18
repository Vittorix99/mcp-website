"use client"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ContactUs } from "@/components/pages/ContactUs"
import { LogoSection } from "@/components/pages/Logo"
import { NextEventSection } from "@/components/pages/NextEventSection"
import { Newsletter } from "@/components/pages/NewsLetter"
import { AboutUs } from "@/components/pages/AboutUs"
import { getNextEvent } from "@/services/events"
import {  useEffect, useState } from "react"

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
  }
  , [])


  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center">
        <LogoSection />
      </section>

      {/* Next Event Section */}
      {hasNextEvent && (
      <section className="py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-black/0 via-mcp-orange/5 to-black/0" />
        <NextEventSection event={nextEvent}/>
      </section>
      )}

      {/* About Section */}
      <section id="about" className="relative py-24">
        <AboutUs />
      </section>

      {/* Join Us Section */}
      <section id="join" className="relative py-24">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-8 gradient-text">Join Our Community</h2>
          <p className="text-lg mb-8 text-gray-300 max-w-2xl mx-auto">
            Become a part of our movement and experience the power of music connection.
          </p>
          <Link href="/subscribe">
            <Button size="lg" className="bg-mcp-gradient hover:opacity-90 text-white border-0">
              Sign Up Now
            </Button>
          </Link>
        </div>
      </section>

      {/* Newsletter Section */}
      <section id="newsletter-section" className="relative py-24 bg-black/50 backdrop-blur-sm">
        <Newsletter />
      </section>

      {/* Contact Section */}
      <section id="contact-section" className="relative py-24">
        <ContactUs />
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-white/10">
        <div className="container mx-auto px-4 text-center text-sm text-gray-400">
          <p>&copy; {new Date().getFullYear()} Music Connecting People. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

