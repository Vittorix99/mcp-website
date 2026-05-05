"use client"

import Image from "next/image"
import { SectionLabel } from "@/components/SectionLabel"
import { useReveal } from "@/hooks/useReveal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const STEPS = [
  {
    n: "01", title: "Buy Your Participation",
    body: "Purchase access to any MCP event through the site. Each event requires a participation fee — no generic ticketing platforms, just a direct connection with the collective.",
  },
  {
    n: "02", title: "Get Your Membership Card",
    body: "Every participant holds an MCP membership card (tessera associativa). If you don't have one yet, it's included with your first purchase. It arrives in your email as an Apple Wallet or Google Wallet pass.",
  },
  {
    n: "03", title: "Event Loaded on Your Card",
    body: "Once confirmed, the event is loaded directly onto your membership card. One card, every MCP event — no printing, no separate tickets.",
  },
  {
    n: "04", title: "Secret Location Revealed",
    body: "We never publish the exact address publicly. After your purchase, you'll receive precise directions to the venue — a detail that's part of the experience itself.",
  },
]

export function HowItWorksSection() {
  useReveal()

  return (
    <section style={{
      background: "#0a0a0a", padding: "120px 0 80px",
      borderTop: "1px solid rgba(245,243,239,0.04)",
    }}>
      <div style={{ maxWidth: "880px", margin: "0 auto", padding: "0 40px" }}>
        <SectionLabel text="How It Works" />

        <h2 style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(32px,4.5vw,60px)", letterSpacing: "-0.03em",
          textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.88,
          marginBottom: "72px",
        }}>
          Participating<br />in an MCP Event
        </h2>

        <div>
          {STEPS.map((s, i) => (
            <div key={i} className={`hiw-step reveal reveal-delay-${Math.min(i + 1, 4)}`}>
              <p style={{
                fontFamily: HN, fontWeight: 700,
                fontSize: "11px", color: ACC, letterSpacing: "0.1em", paddingTop: "5px", margin: 0,
              }}>{s.n}</p>
              <div>
                <h3 style={{
                  fontFamily: HN, fontWeight: 700,
                  fontSize: "20px", letterSpacing: "-0.01em",
                  textTransform: "uppercase", color: "#F5F3EF", marginBottom: "12px",
                }}>{s.title}</h3>
                <p style={{
                  fontFamily: CH, fontSize: "16px",
                  lineHeight: 1.78, color: "rgba(245,243,239,0.52)", margin: 0,
                }}>{s.body}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Tessera + wallet showcase */}
        <div className="hiw-wallet-grid" style={{ marginTop: "60px" }}>
          {/* Card mockup */}
          <div style={{ position: "relative" }}>
            <div style={{
              position: "relative", maxWidth: "300px", margin: "0 auto",
              filter: "drop-shadow(0 24px 60px rgba(0,0,0,0.7))",
            }}>
              <div
                style={{
                  transform: "rotate(-3deg) scale(0.92)",
                  transition: "transform 0.4s ease",
                  borderRadius: "16px", overflow: "hidden",
                }}
                onMouseEnter={e => e.currentTarget.style.transform = "rotate(0deg) scale(1)"}
                onMouseLeave={e => e.currentTarget.style.transform = "rotate(-3deg) scale(0.92)"}
              >
                <Image
                  src="/tessera-mockup.png"
                  alt="MCP Membership Card"
                  width={300}
                  height={190}
                  style={{ width: "100%", display: "block", borderRadius: "16px" }}
                />
              </div>
              <div style={{
                position: "absolute", inset: "-20px",
                background: `radial-gradient(circle, ${ACC}20 0%, transparent 70%)`,
                filter: "blur(30px)", zIndex: -1, borderRadius: "50%",
              }} />
            </div>
          </div>

          {/* Info */}
          <div>
            <p style={{
              fontFamily: HN, fontSize: "8px", fontWeight: 700,
              letterSpacing: "0.35em", textTransform: "uppercase",
              color: ACC, marginBottom: "14px",
            }}>Your Membership Card</p>
            <h3 style={{
              fontFamily: HN, fontWeight: 900, fontSize: "22px",
              letterSpacing: "-0.01em", textTransform: "uppercase",
              color: "#F5F3EF", marginBottom: "16px",
            }}>One card.<br />Every event.</h3>
            <p style={{
              fontFamily: CH, fontSize: "15px", lineHeight: 1.72,
              color: "rgba(245,243,239,0.5)", marginBottom: "24px",
            }}>
              Your tessera associativa arrives as an Apple Wallet or Google Wallet pass.
              Each event you join gets loaded directly onto it — no separate tickets, ever.
            </p>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
              {["Apple Wallet", "Google Wallet"].map(w => (
                <div key={w} style={{
                  padding: "9px 18px",
                  border: "1px solid rgba(245,243,239,0.14)", borderRadius: "6px",
                  fontFamily: HN, fontSize: "10px", letterSpacing: "0.12em",
                  color: "rgba(245,243,239,0.42)",
                  background: "rgba(245,243,239,0.025)",
                }}>{w}</div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
