"use client"

import { useRef, useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { NextEventSection } from "@/components/pages/NextEventSection"
import { HowItWorksSection } from "@/components/pages/HowItWorksSection"
import { AboutUs } from "@/components/pages/AboutUs"
import { RadioSection } from "@/components/pages/RadioSection"
import { ContactUs } from "@/components/pages/ContactUs"
import { WaveDivider } from "@/components/WavePattern"

const ACC = "#E07800"
const RED = "#D10000"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

function HeroSection() {
  const [scrollY, setScrollY] = useState(0)
  const [videoLoaded, setVideoLoaded] = useState(false)
  const videoRef = useRef(null)

  useEffect(() => {
    const fn = () => setScrollY(window.scrollY)
    window.addEventListener("scroll", fn, { passive: true })
    return () => window.removeEventListener("scroll", fn)
  }, [])

  useEffect(() => {
    const v = videoRef.current
    if (!v) return
    v.setAttribute("playsinline", "true")
    v.setAttribute("webkit-playsinline", "true")
    v.setAttribute("muted", "muted")
    v.defaultMuted = true
    v.muted = true
    v.autoplay = true
    const markReady = () => setVideoLoaded(true)
    const tryPlay = () => {
      if (v.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) markReady()
      v.play().catch(() => {})
    }

    tryPlay()
    window.addEventListener("pageshow", tryPlay)
    document.addEventListener("visibilitychange", tryPlay)
    v.addEventListener("loadedmetadata", tryPlay)
    v.addEventListener("loadeddata", markReady)
    v.addEventListener("canplay", tryPlay)
    v.addEventListener("canplaythrough", tryPlay)

    return () => {
      window.removeEventListener("pageshow", tryPlay)
      document.removeEventListener("visibilitychange", tryPlay)
      v.removeEventListener("loadedmetadata", tryPlay)
      v.removeEventListener("loadeddata", markReady)
      v.removeEventListener("canplay", tryPlay)
      v.removeEventListener("canplaythrough", tryPlay)
    }
  }, [])

  const parallax = scrollY * 0.35
  const fadeOut = Math.max(0, 1 - scrollY / 520)
  const videoParallax = scrollY * 0.2

  const scrollToAbout = () => {
    const el = document.getElementById("about-anchor")
    if (el) el.scrollIntoView({ behavior: "smooth" })
  }

  return (
    <section style={{ height: "100svh", position: "relative", overflow: "hidden", background: "#080808" }}>
      {/* Video background */}
      <div style={{
        position: "absolute", inset: 0, overflow: "hidden",
        opacity: videoLoaded ? 1 : 0, transition: "opacity 1.5s ease",
      }}>
        <video
          ref={videoRef}
          muted playsInline loop autoPlay
          preload="auto"
          src="/videos/oneshot.mp4"
          onLoadedMetadata={() => videoRef.current?.play().catch(() => {})}
          onLoadedData={() => setVideoLoaded(true)}
          onCanPlay={() => {
            setVideoLoaded(true)
            videoRef.current?.play().catch(() => {})
          }}
          style={{
            position: "absolute", inset: 0, width: "100%", height: "115%",
            objectFit: "cover",
            transform: `translateY(${videoParallax}px)`,
            filter: "brightness(0.42) saturate(0.75)",
          }}
        />
        <div style={{
          position: "absolute", inset: 0,
          background: "linear-gradient(to bottom, rgba(8,8,8,0.3) 0%, rgba(8,8,8,0.1) 40%, rgba(8,8,8,0.7) 85%, #080808 100%)",
        }} />
      </div>

      {/* Glow orb fallback */}
      {!videoLoaded && (
        <div style={{
          position: "absolute", borderRadius: "50%",
          width: "65vw", height: "65vw", maxWidth: "750px", maxHeight: "750px",
          background: `radial-gradient(circle, ${ACC}18 0%, transparent 68%)`,
          top: "50%", left: "50%",
          transform: `translate(-50%, calc(-50% + ${parallax * 0.25}px))`,
          filter: "blur(70px)", pointerEvents: "none",
        }} />
      )}

      {/* Content */}
      <div className="home-hero-content" style={{
        position: "absolute", inset: 0,
        display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        transform: `translateY(${parallax * 0.45}px)`,
        opacity: fadeOut, padding: "0 24px", textAlign: "center",
        zIndex: 2,
      }}>
        <Image
          className="home-hero-logo"
          src="/logo-full-white.png"
          alt="MCP — Music Connecting People"
          width={350}
          height={90}
          style={{ height: "clamp(48px,8vw,90px)", width: "auto", marginBottom: "44px", opacity: 0.95 }}
          priority
        />

        {/* Giant wordmark */}
        <div className="home-hero-wordmark" style={{ lineHeight: 0.86, textAlign: "center" }}>
          <div>
            <span className="home-hero-word" style={{
              fontFamily: HN, fontWeight: 900,
              fontSize: "clamp(52px,11vw,158px)", letterSpacing: "-0.035em",
              textTransform: "uppercase", color: "#F5F3EF", display: "block",
              textShadow: "0 2px 40px rgba(0,0,0,0.6)",
            }}>music</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "clamp(10px,2vw,24px)" }}>
            <div className="home-hero-dash home-hero-dash--orange" style={{ height: "4px", width: "clamp(28px,4vw,72px)", background: ACC, flexShrink: 0 }} />
            <span className="home-hero-word" style={{
              fontFamily: HN, fontWeight: 900,
              fontSize: "clamp(52px,11vw,158px)", letterSpacing: "-0.035em",
              textTransform: "uppercase", color: "#F5F3EF",
              textShadow: "0 2px 40px rgba(0,0,0,0.6)",
            }}>connecting</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "clamp(10px,2vw,24px)" }}>
            <span className="home-hero-word" style={{
              fontFamily: HN, fontWeight: 900,
              fontSize: "clamp(52px,11vw,158px)", letterSpacing: "-0.035em",
              textTransform: "uppercase", color: "#F5F3EF",
              textShadow: "0 2px 40px rgba(0,0,0,0.6)",
            }}>people</span>
            <div className="home-hero-dash home-hero-dash--red" style={{ height: "4px", width: "clamp(28px,4vw,72px)", background: RED, flexShrink: 0 }} />
          </div>
        </div>

        <p className="home-hero-subtitle" style={{
          fontFamily: CH, fontSize: "clamp(14px,1.5vw,18px)",
          fontStyle: "italic", color: "rgba(245,243,239,0.6)",
          marginTop: "32px", letterSpacing: "0.02em",
          textShadow: "0 1px 12px rgba(0,0,0,0.8)",
        }}>Experience the rhythm. Connect with the community.</p>

        <div className="hero-cta-row" style={{ display: "flex", gap: "14px", marginTop: "40px", flexWrap: "wrap", justifyContent: "center" }}>
          <Link
            href="/events"
            style={{
              padding: "13px 36px", background: ACC,
              borderRadius: "2px", fontFamily: HN, fontWeight: 700,
              fontSize: "10px", letterSpacing: "0.26em", textTransform: "uppercase",
              color: "#fff", textDecoration: "none", display: "inline-block",
            }}
          >Next Events →</Link>
          <button
            onClick={scrollToAbout}
            style={{
              padding: "13px 36px", background: "rgba(0,0,0,0.35)",
              border: "1px solid rgba(245,243,239,0.28)", cursor: "pointer",
              fontFamily: HN, fontWeight: 400,
              fontSize: "10px", letterSpacing: "0.26em", textTransform: "uppercase",
              color: "rgba(245,243,239,0.75)", borderRadius: "2px",
              backdropFilter: "blur(8px)",
            }}
          >Our Story</button>
        </div>
      </div>

      {/* Scroll cue */}
      <div style={{
        position: "absolute", bottom: "28px", left: "50%", transform: "translateX(-50%)",
        opacity: fadeOut * 0.55, display: "flex", flexDirection: "column",
        alignItems: "center", gap: "8px", zIndex: 2,
      }}>
        <p style={{ fontFamily: HN, fontSize: "8px", letterSpacing: "0.45em", textTransform: "uppercase", color: "rgba(245,243,239,0.4)", margin: 0 }}>scroll</p>
        <div style={{ width: "1px", height: "36px", background: "rgba(245,243,239,0.2)", position: "relative", overflow: "hidden" }}>
          <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: "40%", background: ACC, animation: "scrollLine 1.8s ease-in-out infinite" }} />
        </div>
      </div>
    </section>
  )
}

export default function HomeClient({ nextEvent, radioEpisodes }) {
  return (
    <>
      <HeroSection />
      <NextEventSection event={nextEvent} />
      <HowItWorksSection />
      <AboutUs />
      <RadioSection episodes={radioEpisodes || []} />
      <ContactUs />
      <WaveDivider color="rgba(224,120,0,0.18)" scale={1} />
    </>
  )
}
