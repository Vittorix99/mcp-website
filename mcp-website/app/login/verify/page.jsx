"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { isSignInWithEmailLink, signInWithEmailLink } from "firebase/auth"
import { auth } from "@/config/firebase"
import {
  getCurrentMemberRedirect,
  persistMemberSession,
  persistVerifiedMemberSession,
  redirectNeedsServerSession,
  replaceWithMemberRedirect,
} from "@/lib/member-session"
import Link from "next/link"

const MCP_SIGNIN_EMAIL_KEY = "mcp_signin_email"
const MCP_SIGNIN_OOB_PROCESSING_KEY = "mcp_signin_oob_processing"
const OOB_PROCESSING_WINDOW_MS = 15000

const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"

function getOobCode(href) {
  try {
    return new URL(href).searchParams.get("oobCode") || ""
  } catch {
    return ""
  }
}

function claimOobCode(href) {
  if (typeof window === "undefined") return true

  const code = getOobCode(href)
  if (!code) return true

  const now = Date.now()
  let current = null
  try {
    current = JSON.parse(sessionStorage.getItem(MCP_SIGNIN_OOB_PROCESSING_KEY) || "null")
  } catch {
    current = null
  }

  if (
    current?.code === code &&
    now - Number(current?.timestamp || 0) < OOB_PROCESSING_WINDOW_MS
  ) {
    return false
  }

  sessionStorage.setItem(
    MCP_SIGNIN_OOB_PROCESSING_KEY,
    JSON.stringify({ code, timestamp: now })
  )
  return true
}

function releaseOobCode(href) {
  if (typeof window === "undefined") return

  const code = getOobCode(href)
  if (!code) return

  try {
    const current = JSON.parse(sessionStorage.getItem(MCP_SIGNIN_OOB_PROCESSING_KEY) || "null")
    if (current?.code === code) {
      sessionStorage.removeItem(MCP_SIGNIN_OOB_PROCESSING_KEY)
    }
  } catch {
    sessionStorage.removeItem(MCP_SIGNIN_OOB_PROCESSING_KEY)
  }
}

export default function LoginVerifyPage() {
  const completingRef = useRef(false)
  const [redirect, setRedirect] = useState("/dashboard")
  const [status, setStatus] = useState("loading")
  const [emailInput, setEmailInput] = useState("")
  const [error, setError] = useState("")

  const completeSignIn = useCallback(async (email, href, targetRedirect = "/dashboard") => {
    if (completingRef.current || !claimOobCode(href)) return
    completingRef.current = true

    try {
      const result = await signInWithEmailLink(auth, email, href)
      if (redirectNeedsServerSession(targetRedirect)) {
        await persistVerifiedMemberSession(result.user)
      } else {
        persistMemberSession(result.user).catch((err) => {
          console.warn("persistMemberSession optional error:", err)
        })
      }
      localStorage.removeItem(MCP_SIGNIN_EMAIL_KEY)
      replaceWithMemberRedirect(targetRedirect)
    } catch (err) {
      console.error("signInWithEmailLink error:", err)
      if (err?.code === "auth/invalid-action-code" && auth.currentUser) {
        if (redirectNeedsServerSession(targetRedirect)) {
          try {
            await persistVerifiedMemberSession(auth.currentUser)
          } catch (sessionErr) {
            console.error("persistMemberSession after consumed link error:", sessionErr)
            setStatus("error")
            setError("Accesso completato, ma non riesco a salvare la sessione. Controlla che i cookie siano abilitati e riprova.")
            completingRef.current = false
            releaseOobCode(href)
            return
          }
        } else {
          persistMemberSession(auth.currentUser).catch((sessionErr) => {
            console.warn("persistMemberSession optional error:", sessionErr)
          })
        }
        localStorage.removeItem(MCP_SIGNIN_EMAIL_KEY)
        replaceWithMemberRedirect(targetRedirect)
        return
      }

      setStatus("error")
      if (err?.message === "Member session cookie was not stored") {
        setError("Accesso completato, ma non riesco a salvare la sessione. Controlla che i cookie siano abilitati e riprova.")
      } else {
        setError("Link non valido o scaduto. Richiedi un nuovo link.")
      }
      completingRef.current = false
      releaseOobCode(href)
    }
  }, [])

  useEffect(() => {
    if (typeof window === "undefined") return
    const targetRedirect = getCurrentMemberRedirect()
    setRedirect(targetRedirect)

    const href = window.location.href
    if (!isSignInWithEmailLink(auth, href)) {
      setStatus("error")
      setError("Questo link non è valido.")
      return
    }
    const storedEmail = localStorage.getItem(MCP_SIGNIN_EMAIL_KEY)
    if (!storedEmail) {
      setStatus("email_needed")
      return
    }
    completeSignIn(storedEmail, href, targetRedirect)
  }, [completeSignIn])

  function handleEmailSubmit(e) {
    e.preventDefault()
    const trimmed = emailInput.trim().toLowerCase()
    if (!trimmed) return
    setStatus("loading")
    completeSignIn(trimmed, window.location.href, redirect)
  }

  if (status === "loading") {
    return (
      <div className="auth-shell" style={{ alignItems: "center", justifyContent: "center" }}>
        <div style={{ textAlign: "center" }}>
          <p style={{
            fontFamily: HN,
            fontWeight: 900,
            fontSize: "0.875rem",
            color: "#E07800",
            letterSpacing: "0.35em",
            textTransform: "uppercase",
            marginBottom: "2.5rem",
          }}>MCP</p>
          <div style={{
            width: "28px",
            height: "28px",
            border: "2px solid #1a1a1a",
            borderTopColor: "#E07800",
            borderRadius: "50%",
            animation: "spin 0.75s linear infinite",
            margin: "0 auto 1.5rem",
          }} />
          <p style={{
            fontFamily: HN,
            fontWeight: 300,
            fontSize: "0.6875rem",
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.3)",
          }}>Accesso in corso…</p>
        </div>
      </div>
    )
  }

  if (status === "email_needed") {
    return (
      <div className="auth-shell">
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

        <div className="auth-right">
          <div className="auth-form-wrap">
            <div className="auth-accent-bar" />
            <h1 style={{
              fontFamily: HN,
              fontWeight: 900,
              fontSize: "1rem",
              letterSpacing: "0.14em",
              textTransform: "uppercase",
              color: "#ffffff",
              margin: "0 0 0.5rem 0",
            }}>Conferma email</h1>
            <p style={{
              fontFamily: HN,
              fontWeight: 300,
              fontSize: "0.8125rem",
              color: "rgba(255,255,255,0.38)",
              margin: "0 0 2.5rem 0",
              lineHeight: 1.65,
              letterSpacing: "0.02em",
            }}>
              Stai aprendo il link su un dispositivo diverso. Inserisci la tua email per completare l&apos;accesso.
            </p>
            <form onSubmit={handleEmailSubmit} noValidate>
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
                }}>Email</label>
                <input
                  className="auth-input"
                  type="email"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  placeholder="la-tua@email.it"
                  required
                  autoFocus
                />
              </div>
              <button type="submit" className="auth-btn">Conferma →</button>
            </form>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-shell" style={{ alignItems: "center", justifyContent: "center" }}>
      <div style={{ textAlign: "center", maxWidth: "380px", padding: "2rem" }}>
        <p style={{
          fontFamily: HN,
          fontWeight: 900,
          fontSize: "0.875rem",
          color: "#E07800",
          letterSpacing: "0.35em",
          textTransform: "uppercase",
          marginBottom: "2.5rem",
        }}>MCP</p>
        <div className="auth-accent-bar" style={{ margin: "0 auto 1.75rem" }} />
        <h2 style={{
          fontFamily: HN,
          fontWeight: 900,
          fontSize: "1rem",
          letterSpacing: "0.14em",
          textTransform: "uppercase",
          color: "#ffffff",
          margin: "0 0 1rem 0",
        }}>Link non valido</h2>
        <p style={{
          fontFamily: HN,
          fontWeight: 300,
          fontSize: "0.8125rem",
          color: "rgba(255,255,255,0.4)",
          margin: "0 0 2rem 0",
          lineHeight: 1.65,
          letterSpacing: "0.02em",
        }}>{error}</p>
        <Link href={`/login?redirect=${encodeURIComponent(redirect)}`} className="auth-btn" style={{ display: "inline-block", width: "auto", padding: "0.875rem 2rem" }}>
          Richiedi un nuovo link →
        </Link>
      </div>
    </div>
  )
}
