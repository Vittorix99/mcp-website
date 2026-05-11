"use client"

import { useState, useEffect } from "react"
import { sendSignInLinkToEmail, onAuthStateChanged } from "firebase/auth"
import { auth } from "@/config/firebase"
import {
  getCurrentMemberRedirect,
  persistMemberSession,
  persistVerifiedMemberSession,
  redirectNeedsServerSession,
  replaceWithMemberRedirect,
} from "@/lib/member-session"
function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

const MCP_SIGNIN_EMAIL_KEY = "mcp_signin_email"

const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [sent, setSent] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) return
      try {
        const redirect = getCurrentMemberRedirect()
        if (redirectNeedsServerSession(redirect)) {
          await persistVerifiedMemberSession(user)
        } else {
          persistMemberSession(user).catch((err) => {
            console.warn("persistMemberSession optional error:", err)
          })
        }
        replaceWithMemberRedirect(redirect)
      } catch (err) {
        console.error("persistMemberSession error:", err)
        setError("Accesso completato, ma non riesco a salvare la sessione. Controlla che i cookie siano abilitati e riprova.")
      }
    })
    return () => unsubscribe()
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError("")
    const trimmed = email.trim().toLowerCase()
    if (!isValidEmail(trimmed)) {
      setError("Inserisci un indirizzo email valido.")
      return
    }
    setLoading(true)
    try {
      const redirect = getCurrentMemberRedirect()
      const verifyUrl = new URL("/login/verify", window.location.origin)
      verifyUrl.searchParams.set("redirect", redirect)
      const actionCodeSettings = {
        url: verifyUrl.toString(),
        handleCodeInApp: true,
      }
      await sendSignInLinkToEmail(auth, trimmed, actionCodeSettings)
      localStorage.setItem(MCP_SIGNIN_EMAIL_KEY, trimmed)
      setSent(true)
    } catch (err) {
      console.error("sendSignInLinkToEmail error:", err)
      setError("Si è verificato un errore. Controlla l'email e riprova.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      {/* Left — editorial panel */}
      <div className="auth-left">
        <div style={{ position: "relative", zIndex: 1 }}>
          <p style={{
            fontFamily: HN,
            fontWeight: 900,
            fontSize: "clamp(3.5rem, 7vw, 6.5rem)",
            color: "#ffffff",
            letterSpacing: "-0.025em",
            lineHeight: 0.88,
            margin: "0 0 0.1em 0",
            textTransform: "uppercase",
          }}>AREA</p>
          <p style={{
            fontFamily: HN,
            fontWeight: 900,
            fontSize: "clamp(3.5rem, 7vw, 6.5rem)",
            color: "#E07800",
            letterSpacing: "-0.025em",
            lineHeight: 0.88,
            margin: 0,
            textTransform: "uppercase",
          }}>SOCI</p>
          <p style={{
            fontFamily: HN,
            fontWeight: 300,
            fontSize: "0.6875rem",
            letterSpacing: "0.24em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.25)",
            marginTop: "1.75rem",
          }}>Portale riservato ai soci MCP</p>
        </div>

        <p style={{
          fontFamily: HN,
          fontWeight: 300,
          fontSize: "0.625rem",
          letterSpacing: "0.16em",
          textTransform: "uppercase",
          color: "rgba(255,255,255,0.14)",
          margin: 0,
          position: "relative",
          zIndex: 1,
        }}>© MCP {new Date().getFullYear()}</p>
      </div>

      {/* Right — form */}
      <div className="auth-right">
        <div className="auth-form-wrap">
          {sent ? (
            <div>
              <div className="auth-accent-bar" />
              <h1 style={{
                fontFamily: HN,
                fontWeight: 900,
                fontSize: "clamp(1.5rem, 4vw, 2rem)",
                letterSpacing: "-0.01em",
                textTransform: "uppercase",
                color: "#ffffff",
                margin: "0 0 1.25rem 0",
                lineHeight: 1.1,
              }}>
                Controlla<br />la tua inbox
              </h1>
              <p style={{
                fontFamily: HN,
                fontWeight: 300,
                fontSize: "0.875rem",
                letterSpacing: "0.03em",
                color: "rgba(255,255,255,0.42)",
                margin: "0 0 2rem 0",
                lineHeight: 1.7,
              }}>
                Ti abbiamo inviato un link di accesso.<br />
                Controlla anche la cartella spam.
              </p>
              <button
                onClick={() => setSent(false)}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  cursor: "pointer",
                  fontFamily: HN,
                  fontSize: "0.625rem",
                  letterSpacing: "0.22em",
                  textTransform: "uppercase",
                  color: "rgba(224,120,0,0.7)",
                  textDecoration: "underline",
                  textUnderlineOffset: "4px",
                }}
              >
                Usa un'altra email
              </button>
            </div>
          ) : (
            <div>
              <div className="auth-accent-bar" />
              <h2 style={{
                fontFamily: HN,
                fontWeight: 900,
                fontSize: "1rem",
                letterSpacing: "0.14em",
                textTransform: "uppercase",
                color: "#ffffff",
                margin: "0 0 0.5rem 0",
              }}>Accedi</h2>
              <p style={{
                fontFamily: HN,
                fontWeight: 300,
                fontSize: "0.8125rem",
                letterSpacing: "0.02em",
                color: "rgba(255,255,255,0.38)",
                margin: "0 0 2.5rem 0",
                lineHeight: 1.65,
              }}>
                Inserisci la tua email. Ricevi un link magico — nessuna password.
              </p>

              <form onSubmit={handleSubmit} noValidate>
                <div style={{ marginBottom: "2rem" }}>
                  <label style={{
                    display: "block",
                    fontFamily: HN,
                    fontWeight: 700,
                    fontSize: "0.5625rem",
                    letterSpacing: "0.24em",
                    textTransform: "uppercase",
                    color: "rgba(255,255,255,0.32)",
                    marginBottom: "0.875rem",
                  }}>
                    Email
                  </label>
                  <input
                    className="auth-input"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="la-tua@email.it"
                    required
                    autoFocus
                  />
                  {error && (
                    <p style={{
                      fontFamily: HN,
                      fontSize: "0.6875rem",
                      letterSpacing: "0.04em",
                      color: "#D10000",
                      margin: "0.75rem 0 0 0",
                    }}>{error}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="auth-btn"
                >
                  {loading ? "Invio in corso…" : "Invia link di accesso →"}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
