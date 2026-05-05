"use client"

import { useState } from "react"
import Image from "next/image"
import Link from "next/link"
import { sendNewsLetterRequest } from "@/services/newsLetter"
import { legalInfo, socialLinks, iubendaLinks } from "@/config/legal-info"
import { WaveDivider } from "@/components/WavePattern"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const NAV_LINKS = [
  { label: "Events", href: "/events" },
  { label: "Radio", href: "/radio" },
  { label: "Photos", href: "/events-foto" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
]

const labelStyle = {
  fontFamily: HN, fontSize: "8px", fontWeight: 700,
  letterSpacing: "0.35em", textTransform: "uppercase",
  color: ACC, marginBottom: "18px", display: "block",
}

const textStyle = {
  fontFamily: CH, fontSize: "13px", lineHeight: 1.7,
  color: "rgba(245,243,239,0.45)",
}

export function Footer() {
  const [email, setEmail] = useState("")
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleNewsletter = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { success } = await sendNewsLetterRequest({ email })
      if (success) { setDone(true); setEmail("") }
    } catch {}
    finally { setLoading(false) }
  }

  return (
    <footer style={{
      background: "#060606",
      borderTop: "1px solid rgba(224,120,0,0.15)",
      padding: "64px 40px 32px",
    }}>
      <div style={{ maxWidth: "1360px", margin: "0 auto" }}>
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "48px",
          marginBottom: "56px",
        }}>
          {/* Brand */}
          <div>
            <Image
              src="/logo-full-white.png"
              alt="MCP"
              width={160}
              height={46}
              style={{ height: "46px", width: "auto", marginBottom: "18px", opacity: 0.88 }}
            />
            <p style={{ ...textStyle, marginBottom: "18px" }}>
              Music Connecting People.<br />Palermo, Italy.
            </p>
            <div style={{ display: "flex", gap: "16px" }}>
              <a href={socialLinks.instagram} target="_blank" rel="noreferrer" style={{
                fontFamily: HN, fontSize: "10px", letterSpacing: "0.14em",
                color: "rgba(245,243,239,0.38)", textDecoration: "none",
              }}>Instagram ↗</a>
              <a href="https://soundcloud.com/music_connectingpeople" target="_blank" rel="noreferrer" style={{
                fontFamily: HN, fontSize: "10px", letterSpacing: "0.14em",
                color: "rgba(245,243,239,0.38)", textDecoration: "none",
              }}>SoundCloud ↗</a>
            </div>
          </div>

          {/* Navigate */}
          <div>
            <span style={labelStyle}>Navigate</span>
            {NAV_LINKS.map(l => (
              <Link key={l.href} href={l.href} style={{
                display: "block", padding: "0 0 10px",
                fontFamily: HN, fontSize: "12px", letterSpacing: "0.12em",
                color: "rgba(245,243,239,0.5)", textDecoration: "none",
              }}>{l.label}</Link>
            ))}
          </div>

          {/* Newsletter */}
          <div>
            <span style={labelStyle}>Newsletter</span>
            {done ? (
              <p style={{ ...textStyle, fontStyle: "italic", color: ACC }}>
                Thanks — see you on the floor.
              </p>
            ) : (
              <form onSubmit={handleNewsletter} style={{ display: "flex", gap: "8px" }}>
                <input
                  type="email" required value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  disabled={loading}
                  style={{
                    flex: 1, padding: "10px 12px",
                    background: "rgba(255,255,255,0.04)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "2px", color: "#F5F3EF",
                    fontFamily: HN, fontSize: "12px", outline: "none",
                  }}
                />
                <button type="submit" disabled={loading} style={{
                  padding: "10px 16px", background: loading ? "rgba(224,120,0,0.6)" : ACC,
                  border: "none", borderRadius: "2px", cursor: loading ? "default" : "pointer",
                  color: "#fff", fontWeight: 700, fontSize: "13px",
                }}>→</button>
              </form>
            )}
          </div>

          {/* Legal */}
          <div>
            <span style={labelStyle}>Legal</span>
            <p style={{ ...textStyle, fontSize: "12px", lineHeight: 1.75 }}>
              {legalInfo.name}<br />
              {legalInfo.address}<br /><br />
              P.IVA / CF: {legalInfo.vat}<br /><br />
              <a href={iubendaLinks.privacyPolicy} target="_blank" rel="noreferrer"
                 style={{ color: "rgba(245,243,239,0.3)", fontSize: "11px" }}>Privacy Policy</a><br />
              <a href={iubendaLinks.cookiePolicy} target="_blank" rel="noreferrer"
                 style={{ color: "rgba(245,243,239,0.3)", fontSize: "11px" }}>Cookie Policy</a>
            </p>
          </div>
        </div>

        <WaveDivider color="rgba(224,120,0,0.18)" scale={0.55} />
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          paddingTop: "22px", flexWrap: "wrap", gap: "8px",
        }}>
          <p style={{ fontFamily: HN, fontSize: "9px", letterSpacing: "0.2em", textTransform: "uppercase", color: "rgba(245,243,239,0.2)", margin: 0 }}>
            © 2026 Music Connecting People ETS
          </p>
          <p style={{ fontFamily: CH, fontSize: "11px", fontStyle: "italic", color: "rgba(245,243,239,0.15)", margin: 0 }}>
            "Experience the rhythm. Connect with the community."
          </p>
        </div>
      </div>
    </footer>
  )
}
