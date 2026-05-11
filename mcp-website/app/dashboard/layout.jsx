"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { signOut } from "firebase/auth"
import { auth } from "@/config/firebase"
import { useUser } from "@/contexts/userContext"
import { clearMemberSession, persistMemberSession } from "@/lib/member-session"
import Link from "next/link"

const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"

export default function DashboardLayout({ children }) {
  const { user, loading } = useUser()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login?redirect=/dashboard")
    } else if (!loading && user) {
      persistMemberSession(auth.currentUser).catch((err) => {
        console.error("persistMemberSession error:", err)
      })
    }
  }, [user, loading, router])

  async function handleLogout() {
    try {
      await signOut(auth)
      await clearMemberSession()
      router.replace("/login")
    } catch (err) {
      console.error("logout error:", err)
    }
  }

  if (loading) {
    return (
      <div style={{
        minHeight: "100vh",
        backgroundColor: "#080808",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}>
        <div style={{
          width: "28px",
          height: "28px",
          border: "2px solid #1a1a1a",
          borderTopColor: "#E07800",
          borderRadius: "50%",
          animation: "spin 0.75s linear infinite",
        }} />
      </div>
    )
  }

  if (!user) return null

  return (
    <div className="dash-shell">
      <header className="dash-topbar">
        <div style={{ display: "flex", alignItems: "center", gap: "1.25rem" }}>
          <Link href="/" style={{ textDecoration: "none" }}>
            <span style={{
              fontFamily: HN,
              fontWeight: 900,
              fontSize: "0.875rem",
              color: "#E07800",
              letterSpacing: "0.32em",
              textTransform: "uppercase",
            }}>MCP</span>
          </Link>
          <span style={{
            fontFamily: HN,
            fontWeight: 300,
            fontSize: "0.5625rem",
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "rgba(255,255,255,0.2)",
          }}>/ Area soci</span>
        </div>
        <button onClick={handleLogout} className="dash-logout-btn">
          Esci
        </button>
      </header>
      <main className="dash-main">{children}</main>
    </div>
  )
}
