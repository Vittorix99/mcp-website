"use client"

import { useRef, useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { LogoSection } from "@/components/pages/Logo"
import { Volume, VolumeX } from "lucide-react"

const CONFIG = {
  wrapperHeight: "120svh",
  audioUnlockProgress: 0.3,
  logoFadeMultiplier: 3.5,
  videoStartOffset: 0.05,
  videoFadeMultiplier: 1.7,
  logoTranslateY: 40,
  videoScaleRange: 0.03,
  hintFadeMultiplier: 1,
  heroCompleteVideoOpacity: 0.98,
  heroCompleteLogoOpacity: 0.02,
  intersectionThreshold: 0.05,
  overlayGradient:
    "linear-gradient(to bottom, rgba(0,0,0,0.15), rgba(0,0,0,0.25))",
}

/* -------------------------------------------------------
   MOBILE HERO → VIDEO (smooth + autoplay iOS)
   - progress senza reflow (scrollY/offsetTop)
   - layer GPU (translateZ(0))
   - autoplay iOS: defaultMuted + playsInline + webkit-playsinline
   - mute automatico quando la sezione non è visibile
--------------------------------------------------------*/
export function MobileHeroVideoSmooth() {
  const wrapperRef = useRef(null)
  const stickyRef = useRef(null)
  const videoEl = useRef(null)

  const [progress, setProgress] = useState(0) // 0..1
  const [reduceMotion, setReduceMotion] = useState(false)
  const [isMuted, setIsMuted] = useState(true)

  // ---- CONFIG: soglia oltre la quale è permesso togliere il mute ----
  const canToggleAudio = progress >= CONFIG.audioUnlockProgress

  // cache viewport height e offsetTop (evita reflow continui)
  const vhRef = useRef(1)
  const topRef = useRef(0)
  const scrollRangeRef = useRef(1)

  useEffect(() => {
    const updateMetrics = () => {
      vhRef.current = Math.max(1, window.innerHeight || 1)
      const el = wrapperRef.current
      topRef.current = el ? el.offsetTop : 0
      const wrapperHeight = el ? el.offsetHeight : vhRef.current
      scrollRangeRef.current = Math.max(1, wrapperHeight - vhRef.current)
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
        const p = Math.min(1, Math.max(0, scrolled / scrollRangeRef.current))
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
  const logoPhase = 1 - clamp(progress * CONFIG.logoFadeMultiplier) // 0..0.5
  const videoPhase = clamp(
    (progress - CONFIG.videoStartOffset) * CONFIG.videoFadeMultiplier
  ) // 0.15..1 → 0..1 (fade più lento)
  const logoOpacity = reduceMotion ? 0 : logoPhase
  const logoTranslateY = reduceMotion ? 0 : (1 - logoPhase) * -CONFIG.logoTranslateY
  const videoOpacity = reduceMotion ? 1 : Math.max(0.001, videoPhase)
  const videoScale =
    reduceMotion ? 1 : 1 + (1 - videoPhase) * CONFIG.videoScaleRange
  const hintOpacity = clamp(1 - progress * CONFIG.hintFadeMultiplier)
  const isVideoFullyVisible = reduceMotion || videoPhase >= 1

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
      { threshold: CONFIG.intersectionThreshold }
    )
    io.observe(el)
    return () => io.disconnect()
  }, [])

  // Mute forzato quando il logo è ancora ben visibile
  useEffect(() => {
    if (progress < CONFIG.audioUnlockProgress && !isMuted) {
      setIsMuted(true)
    }
  }, [progress, isMuted])

  const toggleAudio = () => {
    if (!canToggleAudio) return // blocca prima della soglia
    setIsMuted((m) => !m)
  }

  // Blocca lo scroll oltre l'hero finché il video ha sostituito il logo
  useEffect(() => {
    const clampScroll = () => {
      if (isVideoFullyVisible) return
      const maxY = topRef.current + scrollRangeRef.current
      if (window.scrollY > maxY) {
        window.scrollTo(0, maxY)
      }
    }
    clampScroll()
    window.addEventListener("scroll", clampScroll, { passive: true })
    return () => window.removeEventListener("scroll", clampScroll)
  }, [isVideoFullyVisible])

  return (
    <section
      ref={wrapperRef}
      className="relative w-full"
      style={{ height: CONFIG.wrapperHeight }}
    >
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
        <div className="absolute inset-0   h-[110svh] overflow-hidden">
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
              background: CONFIG.overlayGradient,
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

     
      </div>
    </section>
  )
}
