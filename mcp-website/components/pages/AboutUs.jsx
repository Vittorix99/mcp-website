"use client"

import { useEffect, useState } from "react"
import Image from "next/image"
import { Ticker } from "@/components/Ticker"
import { SectionLabel } from "@/components/SectionLabel"
import { useReveal } from "@/hooks/useReveal"
import { getImageUrls, getImageUrlsFromBucket } from "@/config/firebaseStorage"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const PHOTOS = [
  { bg: "#2a1808", label: "Club atmosphere" },
  { bg: "#0c0c22", label: "DJ set · dancefloor" },
  { bg: "#220a10", label: "Crowd · connection" },
  { bg: "#181806", label: "Light show" },
]
const SHOWCASE_FOLDER = "foto/showcase"
const SHOWCASE_PROD_BUCKET =
  process.env.NEXT_PUBLIC_SHOWCASE_STORAGE_BUCKET || "mcp-website-2a1ad.firebasestorage.app"

function pickRandomImages(urls, count) {
  const shuffled = [...urls]
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    const current = shuffled[i]
    shuffled[i] = shuffled[j]
    shuffled[j] = current
  }
  return shuffled.slice(0, count)
}

export function AboutUs() {
  const [showcaseImages, setShowcaseImages] = useState([])
  useReveal()

  useEffect(() => {
    let alive = true

    async function loadShowcaseImages() {
      try {
        let urls = await getImageUrls(SHOWCASE_FOLDER)
        if (urls.length === 0 && process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET !== SHOWCASE_PROD_BUCKET) {
          urls = await getImageUrlsFromBucket(SHOWCASE_FOLDER, SHOWCASE_PROD_BUCKET)
        }
        if (!alive) return
        setShowcaseImages(pickRandomImages(urls.filter(Boolean), PHOTOS.length))
      } catch (error) {
        console.error("Error fetching showcase images:", error)
      }
    }

    loadShowcaseImages()
    return () => {
      alive = false
    }
  }, [])

  return (
    <section id="about-anchor" style={{ background: "#080808", paddingTop: "120px" }}>
      <Ticker
        items={["Music Connecting People", "Palermo", "Electronic", "Underground", "Community", "Since 2022"]}
        color="rgba(224,120,0,0.35)"
        speed={36}
      />

      <div className="about-inner">
        <div className="about-grid">
          {/* Text */}
          <div className="reveal">
            <SectionLabel text="Our Philosophy" />
            <h2 style={{
              fontFamily: HN, fontWeight: 900,
              fontSize: "clamp(36px,4vw,58px)", letterSpacing: "-0.03em",
              textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.88,
              marginBottom: "36px",
            }}>
              Where music<br />becomes<br />connection
            </h2>
            <p style={{ fontFamily: CH, fontSize: "17px", lineHeight: 1.82, color: "rgba(245,243,239,0.62)", marginBottom: "22px" }}>
              Music Connecting People was born to find a safe, emotionally immersive, sonorously and visually stunning way of partying.
            </p>
            <p style={{ fontFamily: CH, fontSize: "16px", lineHeight: 1.82, color: "rgba(245,243,239,0.48)", marginBottom: "36px" }}>
              We believe that through music, it is possible to reconnect with our inner essence and share it in real life. Electronic music offers not only the best journey when celebrating but also a way of self-reconciliation and embracing new horizons.
            </p>
            <blockquote style={{ borderLeft: `2px solid ${ACC}`, paddingLeft: "22px", marginBottom: "40px" }}>
              <p style={{ fontFamily: CH, fontSize: "15px", fontStyle: "italic", lineHeight: 1.78, color: "rgba(245,243,239,0.4)", margin: 0 }}>
                "We are drawn toward the future, while finding a guide in the past, lost in the present."
              </p>
            </blockquote>
            <Image
              src="/patterns/pattern-orange.png"
              alt=""
              width={200}
              height={24}
              style={{ height: "24px", width: "auto", opacity: 0.6 }}
            />
          </div>

          {/* Photo grid */}
          <div className="about-photos-grid reveal reveal-delay-2">
            {PHOTOS.map((p, i) => {
              const src = showcaseImages[i]
              return (
                <div key={p.label} style={{
                  background: p.bg, position: "relative", overflow: "hidden",
                  gridColumn: i === 0 ? "1/3" : "auto",
                  borderTop: i === 0 ? `3px solid ${ACC}` : "none",
                }}>
                  {src && (
                    <Image
                      src={src}
                      alt={p.label}
                      fill
                      sizes={i === 0 ? "(max-width: 768px) 100vw, 50vw" : "(max-width: 768px) 50vw, 25vw"}
                      style={{ objectFit: "cover" }}
                      priority={i === 0}
                      unoptimized
                    />
                  )}
                  <div style={{
                    position: "absolute", inset: 0,
                    background: "linear-gradient(to bottom, rgba(8,8,8,0.05), rgba(8,8,8,0.3))",
                  }} />
                  <div style={{
                    position: "absolute", inset: 0,
                    backgroundImage: `repeating-linear-gradient(45deg,
                      rgba(255,255,255,0.012) 0px,rgba(255,255,255,0.012) 1px,
                      transparent 1px,transparent 18px)`,
                  }} />
                  <div style={{
                    position: "absolute", bottom: "10px", left: "12px",
                    fontFamily: HN, fontSize: "7px",
                    letterSpacing: "0.22em", textTransform: "uppercase",
                    color: "rgba(245,243,239,0.32)",
                  }}>{p.label}</div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
