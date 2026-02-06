"use client"

import { useMemo, useRef, useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { LogoSection } from "@/components/pages/Logo"
import { NextEventSection } from "@/components/pages/NextEventSection"
import { AboutUs } from "@/components/pages/AboutUs"
import { ContactUs } from "@/components/pages/ContactUs"
import { AnimatedSectionDivider } from "@/components/AnimatedSectionDivider"
import { SectionTitle } from "@/components/ui/section-title"
 
import { Volume, VolumeX } from "lucide-react"
import { getNextEvent } from "@/services/events"

/* -------------------------------------------------------
   MOBILE HERO → VIDEO (smooth + autoplay iOS)
   - progress senza reflow (scrollY/offsetTop)
   - layer GPU (translateZ(0))
   - autoplay iOS: defaultMuted + playsInline + webkit-playsinline
   - mute automatico quando la sezione non è visibile
--------------------------------------------------------*/
function MobileHeroVideoSmooth() {
  const wrapperRef = useRef(null)
  const stickyRef = useRef(null)
  const videoEl = useRef(null)

  const [progress, setProgress] = useState(0) // 0..1
  const [reduceMotion, setReduceMotion] = useState(false)
  const [isMuted, setIsMuted] = useState(true)

  // ---- CONFIG: soglia oltre la quale è permesso togliere il mute ----
  const AUDIO_UNLOCK_PROGRESS = 0.55 // ~seconda metà: video domina
  const canToggleAudio = progress >= AUDIO_UNLOCK_PROGRESS

  // cache viewport height e offsetTop (evita reflow continui)
  const vhRef = useRef(1)
  const topRef = useRef(0)

  useEffect(() => {
    const updateMetrics = () => {
      vhRef.current = Math.max(1, window.innerHeight || 1)
      const el = wrapperRef.current
      topRef.current = el ? el.offsetTop : 0
    }
    updateMetrics()
    window.addEventListener("resize", updateMetrics)
    window.addEventListener("orientationchange", updateMetrics)
    return () => {
      window.removeEventListener("resize", updateMetrics)
      window.removeEventListener("orientationchange", updateMetrics)
    }
  }, [])

  // prefers-reduced-motion
  useEffect(() => {
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)")
    const update = () => setReduceMotion(!!mql.matches)
    update()
    mql.addEventListener?.("change", update)
    return () => mql.removeEventListener?.("change", update)
  }, [])

  // progress con rAF (NO getBoundingClientRect)
  useEffect(() => {
    let ticking = false
    const onScroll = () => {
      if (ticking) return
      ticking = true
      requestAnimationFrame(() => {
        const scrolled = window.scrollY - topRef.current
        const p = Math.min(1, Math.max(0, scrolled / vhRef.current))
        setProgress(p)
        ticking = false
      })
    }
    onScroll() // init
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  const clamp = (v, min = 0, max = 1) => Math.min(max, Math.max(min, v))

  // mappa 2 fasi
  const logoPhase = 1 - clamp(progress * 2) // 0..0.5
  const videoPhase = clamp((progress - 0.25) * 1.3333) // 0.25..1 → 0..1
  const logoOpacity = reduceMotion ? 0 : logoPhase
  const logoTranslateY = reduceMotion ? 0 : (1 - logoPhase) * -40
  const videoOpacity = reduceMotion ? 1 : Math.max(0.001, videoPhase)
  const videoScale = reduceMotion ? 1 : 1 + (1 - videoPhase) * 0.03
  const hintOpacity = clamp(1 - progress * 2)

  // Autoplay iOS: set attr + tryPlay
  useEffect(() => {
    const v = videoEl.current
    if (!v) return
    v.setAttribute("playsinline", "true")
    v.setAttribute("webkit-playsinline", "true")
    v.setAttribute("x-webkit-airplay", "deny")
    v.setAttribute("muted", "muted")
    v.defaultMuted = true
    v.muted = true
    v.autoplay = true
    v.controls = false
    v.disableRemotePlayback = true

    const tryPlay = () => v.play().catch(() => {})
    tryPlay()
    const onLoadedMeta = () => tryPlay()
    const onCanPlay = () => tryPlay()
    v.addEventListener("loadedmetadata", onLoadedMeta)
    v.addEventListener("canplay", onCanPlay)
    return () => {
      v.removeEventListener("loadedmetadata", onLoadedMeta)
      v.removeEventListener("canplay", onCanPlay)
    }
  }, [])

  // Allinea mute del DOM allo state
  useEffect(() => {
    const v = videoEl.current
    if (!v) return
    v.muted = isMuted
    if (!isMuted) v.play().catch(() => {})
  }, [isMuted])

  // Mute quando la sticky esce dal viewport
  useEffect(() => {
    const el = stickyRef.current
    if (!el) return
    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) setIsMuted(true)
      },
      { threshold: 0.05 }
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  //  Mute forzato quando il logo è ancora ben visibile
  useEffect(() => {
    if (progress < AUDIO_UNLOCK_PROGRESS && !isMuted) {
      setIsMuted(true)
    }
  }, [progress, isMuted])

  const toggleAudio = () => {
    if (!canToggleAudio) return // blocca prima della soglia
    setIsMuted((m) => !m)
  }

  return (
    <section ref={wrapperRef} className="relative h-[120svh] w-full">
      <div ref={stickyRef} className="sticky top-0 h-screen w-full z-[70]">
        {/* LOGO layer */}
        <div
          className="absolute inset-0 flex items-center justify-center pointer-events-none"
          style={{
            opacity: logoOpacity,
            transform: `translateY(${logoTranslateY}px) translateZ(0)`,
            willChange: "transform, opacity",
          }}
        >
          <LogoSection />
        </div>

        {/* VIDEO layer */}
        <div className="absolute inset-0 overflow-hidden">
          <video
            ref={videoEl}
            className="absolute inset-0 w-full h-full object-cover"
            src="/videos/oneshot.mp4"
            autoPlay
            muted
            playsInline
            loop
            preload="auto"
            controls={false}
            controlsList="nodownload noplaybackrate noremoteplayback nofullscreen"
            disablePictureInPicture
            x-webkit-airplay="deny"
            webkit-playsinline="true"
            style={{
              opacity: videoOpacity,
              transform: `scale(${videoScale}) translateZ(0)`,
              willChange: "transform, opacity",
              WebkitTransform: `scale(${videoScale}) translateZ(0)`,
            }}
            onTouchStart={() => {
              videoEl.current?.play().catch(() => {})
            }}
          />

          {/* overlay leggero per contrasto */}
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              background: "linear-gradient(to bottom, rgba(0,0,0,0.15), rgba(0,0,0,0.25))",
              opacity: videoOpacity,
            }}
          />

          {/* Toggle Audio — visibile/attivo solo dopo la soglia */}
          <div
            className="absolute right-3 bottom-16 z-10"
            style={{
              opacity: canToggleAudio ? videoOpacity : 0, // nascondi prima della soglia
              transform: "translateZ(0)",
              pointerEvents: canToggleAudio ? "auto" : "none",
            }}
          >
            <Button
              onClick={toggleAudio}
              size="sm"
              variant="secondary"
              className={`rounded-full text-white border border-white/30 p-2 backdrop-blur-sm ${
                isMuted ? "bg-black/50 hover:bg-black/70" : "bg-black/60 hover:bg-black/80"
              }`}
              aria-label={isMuted ? "Attiva audio" : "Disattiva audio"}
              aria-pressed={!isMuted}
              disabled={!canToggleAudio}
            >
              {isMuted ? <VolumeX size={20} /> : <Volume size={20} />}
            </Button>
          </div>
        </div>

        {/* Hint scroll */}
        <div
          className="absolute bottom-5 left-1/2 -translate-x-1/2 text-[10px] tracking-widest text-white/70"
          style={{ opacity: clamp(1 - progress * 2), transform: "translateZ(0)" }}
        >
          SCROLL
        </div>
      </div>
    </section>
  )
}

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
