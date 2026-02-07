"use client"

import { useMemo, useRef, useState, useEffect } from "react"
import { LogoSection } from "@/components/pages/Logo"
import { NextEventSection } from "@/components/pages/NextEventSection"
import { AboutUs } from "@/components/pages/AboutUs"
import { ContactUs } from "@/components/pages/ContactUs"
import { AnimatedSectionDivider } from "@/components/AnimatedSectionDivider"
import { MobileHeroVideoSmooth } from "@/components/pages/MobileHeroVideoSmooth"
import { getNextEvent } from "@/services/events"

export default function HomeClient({ nextEvent = null, hasNextEvent = false } = {}) {
  const [clientNextEvent, setClientNextEvent] = useState(nextEvent || null)
  const [clientHasNextEvent, setClientHasNextEvent] = useState(!!hasNextEvent)
  const fetchStartedRef = useRef(false)

  const pageClass = useMemo(() => `min-h-screen font-helvetica`, [])

  useEffect(() => {
    if (clientHasNextEvent || clientNextEvent || fetchStartedRef.current) return
    fetchStartedRef.current = true
    let alive = true
    ;(async () => {
      try {
        const { success, events } = await getNextEvent()
        if (!alive) return
        if (success && Array.isArray(events) && events.length > 0) {
          setClientNextEvent(events[0])
          setClientHasNextEvent(true)
        }
      } catch {
        // No-op: landing can render without next event
      }
    })()
    return () => {
      alive = false
    }
  }, [clientHasNextEvent, clientNextEvent])

  return (
    <div className={pageClass}>
      <div className="block md:hidden">
        <MobileHeroVideoSmooth />
      </div>
      <section className="relative h-screen items-center justify-center hidden md:flex">
        <LogoSection />
      </section>

      <AnimatedSectionDivider color="ORANGE" />

      {clientHasNextEvent && (
        <>
          <section className="py-12 md:py-24 relative">
            <div className="absolute inset-0 bg-gradient-to-b from-black/0 via-mcp-orange/5 to-black/0" />
            <NextEventSection event={clientNextEvent} />
          </section>
          <AnimatedSectionDivider color="RED" />
        </>
      )}

      <section id="about" className="relative py-12 md:py-24">
        <AboutUs />
      </section>

      <AnimatedSectionDivider color="ORANGE" />

      <section id="contact-section" className="relative py-12 md:py-24">
        <ContactUs />
      </section>
    </div>
  )
}
