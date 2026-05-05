"use client"

import Image from "next/image"
import { SectionLabel } from "@/components/SectionLabel"
import { useReveal } from "@/hooks/useReveal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"
const CH = "var(--font-charter), Georgia, serif"

const STEPS = [
  {
    n: "01", title: "Acquista la partecipazione",
    body: "Prenota l'accesso agli eventi MCP direttamente dal sito. Ogni evento prevede una quota di partecipazione: niente piattaforme esterne, solo un contatto diretto con il collettivo.",
  },
  {
    n: "02", title: "Ricevi la tessera MCP",
    body: "Ogni partecipante ha una tessera associativa MCP. Se non ne hai ancora una, viene inclusa nel primo acquisto e arriva via email come pass Apple Wallet o Google Wallet.",
  },
  {
    n: "03", title: "L'evento viene caricato sulla tessera",
    body: "Dopo la conferma, l'evento viene associato direttamente alla tua tessera. Una sola card per tutti gli eventi MCP: niente stampe, niente biglietti separati.",
  },
  {
    n: "04", title: "Ricevi la location",
    body: "Non pubblichiamo mai l'indirizzo esatto in modo pubblico. Dopo l'acquisto riceverai le indicazioni precise per raggiungere il luogo dell'evento.",
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
        <SectionLabel text="Come funziona" />

        <h2 style={{
          fontFamily: HN, fontWeight: 900,
          fontSize: "clamp(32px,4.5vw,60px)", letterSpacing: "-0.03em",
          textTransform: "uppercase", color: "#F5F3EF", lineHeight: 0.88,
          marginBottom: "72px",
        }}>
          Partecipare<br />a un evento MCP
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
                  alt="Tessera MCP"
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
            }}>La tua tessera MCP</p>
            <h3 style={{
              fontFamily: HN, fontWeight: 900, fontSize: "22px",
              letterSpacing: "-0.01em", textTransform: "uppercase",
              color: "#F5F3EF", marginBottom: "16px",
            }}>Una tessera.<br />Ogni evento.</h3>
            <p style={{
              fontFamily: CH, fontSize: "15px", lineHeight: 1.72,
              color: "rgba(245,243,239,0.5)", marginBottom: "24px",
            }}>
              La tessera associativa arriva come pass Apple Wallet o Google Wallet.
              Ogni evento a cui partecipi viene caricato direttamente sulla tessera: niente biglietti separati.
            </p>
            <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
              <Image
                src="/apple_wallet.png"
                alt="Apple Wallet"
                width={142}
                height={44}
                style={{ height: "40px", width: "auto", display: "block" }}
              />
              <Image
                src="/google_wallet.png"
                alt="Google Wallet"
                width={142}
                height={44}
                style={{ height: "40px", width: "auto", display: "block" }}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
