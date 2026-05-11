"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useUser } from "@/contexts/userContext"
import { logout } from "@/config/firebase"
import { routes } from "@/config/routes"
import LoginModal from "@/components/auth/LoginModal"

const ACC = "#E07800"
const HN = "var(--font-helvetica), Helvetica, Arial, sans-serif"

const NAV_LINKS = [
  { label: "Events", href: "/events" },
  { label: "Radio", href: "/radio" },
  { label: "Photos", href: "/events-foto" },
  { label: "About", href: "/about" },
  { label: "Contact", href: "/contact" },
]

export const Navigation = () => {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [loginOpen, setLoginOpen] = useState(false)
  const pathname = usePathname()
  const { user, isAdmin } = useUser()

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 40)
    window.addEventListener("scroll", fn, { passive: true })
    return () => window.removeEventListener("scroll", fn)
  }, [])

  useEffect(() => {
    if (menuOpen) document.body.style.overflow = "hidden"
    else document.body.style.overflow = ""
    return () => { document.body.style.overflow = "" }
  }, [menuOpen])

  const handleLogout = async () => {
    try { await logout() } catch {}
    setMenuOpen(false)
  }

  const isActive = (href) => {
    if (href === "/events") return pathname?.startsWith("/events") && !pathname?.startsWith("/events-foto")
    if (href === "/events-foto") return pathname?.startsWith("/events-foto")
    return pathname === href
  }

  return (
    <>
      <nav
        className="site-nav"
        style={{
          position: "fixed", top: 0, left: 0, right: 0, zIndex: 200,
          padding: "14px 32px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          transition: "all 0.35s ease",
          background: scrolled ? "rgba(8,8,8,0.96)" : "transparent",
          borderBottom: scrolled ? "1px solid rgba(224,120,0,0.12)" : "none",
          backdropFilter: scrolled ? "blur(14px)" : "none",
        }}
      >
        {/* Logo */}
        <Link href="/" className="site-nav-logo" style={{ display: "inline-flex", padding: 0 }}>
          <Image
            src="/logo-white.png"
            alt="MCP"
            width={44}
            height={44}
            style={{ height: "40px", width: "auto" }}
            priority
          />
        </Link>

        {/* Desktop links */}
        <div className="nav-desktop-new site-nav-links" style={{ alignItems: "center", gap: "4px" }}>
          {NAV_LINKS.map(l => (
            <Link
              className="site-nav-link"
              key={l.href}
              href={l.href}
              style={{
                background: "none",
                padding: "8px 18px",
                fontFamily: HN, fontWeight: 400,
                fontSize: "10px", letterSpacing: "0.26em", textTransform: "uppercase",
                color: isActive(l.href) ? ACC : "#F5F3EF",
                opacity: isActive(l.href) ? 1 : 0.7,
                borderBottom: isActive(l.href) ? `1px solid ${ACC}` : "1px solid transparent",
                transition: "all 0.2s",
                textDecoration: "none",
                display: "inline-block",
              }}
              onMouseEnter={e => {
                if (!isActive(l.href)) {
                  e.currentTarget.style.opacity = "1"
                  e.currentTarget.style.color = "#F5F3EF"
                }
              }}
              onMouseLeave={e => {
                if (!isActive(l.href)) {
                  e.currentTarget.style.opacity = "0.7"
                  e.currentTarget.style.color = "#F5F3EF"
                }
              }}
            >
              {l.label}
            </Link>
          ))}

          <Link
            className="site-nav-ticket"
            href="/events"
            style={{
              marginLeft: "20px", padding: "10px 24px",
              background: ACC, borderRadius: "2px",
              fontFamily: HN, fontWeight: 700,
              fontSize: "10px", letterSpacing: "0.26em", textTransform: "uppercase",
              color: "#fff", textDecoration: "none",
              display: "inline-block", transition: "opacity 0.2s",
            }}
            onMouseEnter={e => e.currentTarget.style.opacity = "0.85"}
            onMouseLeave={e => e.currentTarget.style.opacity = "1"}
          >
            Get Tickets
          </Link>

          {!user && (
            <>
              <Link
                href="/login"
                style={{
                  marginLeft: "8px", padding: "10px 16px",
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.14)",
                  borderRadius: "2px",
                  fontFamily: HN, fontSize: "9px", letterSpacing: "0.22em", textTransform: "uppercase",
                  color: "rgba(245,243,239,0.62)", textDecoration: "none",
                  display: "inline-block", transition: "all 0.2s",
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.color = "#F5F3EF"
                  e.currentTarget.style.borderColor = "rgba(224,120,0,0.35)"
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.color = "rgba(245,243,239,0.62)"
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.14)"
                }}
              >
                Area soci
              </Link>
              <button
                type="button"
                aria-label="Login staff"
                onClick={() => setLoginOpen(true)}
                style={{
                  marginLeft: "0", padding: "10px 12px",
                  background: "none",
                  border: "1px solid rgba(255,255,255,0.08)",
                  borderRadius: "2px",
                  cursor: "pointer",
                  fontFamily: HN, fontSize: "9px", letterSpacing: "0.18em", textTransform: "uppercase",
                  color: "rgba(245,243,239,0.36)",
                  display: "inline-block", transition: "all 0.2s",
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.color = "#F5F3EF"
                  e.currentTarget.style.borderColor = "rgba(224,120,0,0.28)"
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.color = "rgba(245,243,239,0.36)"
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.08)"
                }}
              >
                Staff
              </button>
            </>
          )}

          {user && !isAdmin && (
            <Link
              href="/dashboard"
              style={{
                marginLeft: "8px", padding: "10px 16px",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.14)",
                borderRadius: "2px",
                fontFamily: HN, fontSize: "9px", letterSpacing: "0.22em", textTransform: "uppercase",
                color: "rgba(245,243,239,0.62)", textDecoration: "none",
                display: "inline-block",
              }}
            >
              Area soci
            </Link>
          )}

          {user && isAdmin && (
            <Link
              className="site-nav-auth"
              href={routes.admin.dashboard}
              style={{
                marginLeft: "8px", padding: "8px 12px",
                background: "rgba(255,255,255,0.06)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "2px",
                fontFamily: HN, fontSize: "9px", letterSpacing: "0.22em", textTransform: "uppercase",
                color: "rgba(245,243,239,0.6)", textDecoration: "none",
                display: "inline-block",
              }}
            >
              Admin
            </Link>
          )}
        </div>

        {/* Mobile burger */}
        <button
          className="nav-burger-new"
          onClick={() => setMenuOpen(!menuOpen)}
          style={{
            background: "none",
            border: "1px solid rgba(255,255,255,0.18)",
            borderRadius: "2px", cursor: "pointer",
            padding: "8px 10px",
            flexDirection: "column", gap: "5px",
          }}
        >
          {[0, 1, 2].map(i => (
            <span key={i} style={{
              display: "block", width: "20px", height: "2px", background: "#F5F3EF",
              transition: "all 0.25s",
              transform: menuOpen && i === 0 ? "rotate(45deg) translate(5px,5px)" :
                         menuOpen && i === 1 ? "scaleX(0)" :
                         menuOpen && i === 2 ? "rotate(-45deg) translate(5px,-5px)" : "none",
              opacity: menuOpen && i === 1 ? 0 : 1,
            }} />
          ))}
        </button>
      </nav>

      {/* Mobile fullscreen overlay */}
      {menuOpen && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 199,
          background: "#080808",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center",
          gap: "8px",
        }}>
          {NAV_LINKS.map(l => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() => setMenuOpen(false)}
              style={{
                background: "none", padding: "10px",
                fontFamily: HN, fontWeight: 900,
                fontSize: "36px", letterSpacing: "0.06em", textTransform: "uppercase",
                color: isActive(l.href) ? ACC : "#F5F3EF",
                textDecoration: "none", display: "block",
              }}
            >
              {l.label}
            </Link>
          ))}

          <Link
            href="/events"
            onClick={() => setMenuOpen(false)}
            style={{
              marginTop: "28px", padding: "14px 48px",
              background: ACC, borderRadius: "2px",
              fontFamily: HN, fontWeight: 700,
              fontSize: "12px", letterSpacing: "0.24em", textTransform: "uppercase",
              color: "#fff", textDecoration: "none", display: "block",
            }}
          >
            Get Tickets
          </Link>

          {user ? (
            <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" }}>
              {isAdmin ? (
                <Link
                  href={routes.admin.dashboard}
                  onClick={() => setMenuOpen(false)}
                  style={{
                    fontFamily: HN, fontSize: "11px", letterSpacing: "0.22em", textTransform: "uppercase",
                    color: "rgba(245,243,239,0.45)", textDecoration: "none",
                  }}
                >Admin Panel</Link>
              ) : (
                <Link
                  href="/dashboard"
                  onClick={() => setMenuOpen(false)}
                  style={{
                    fontFamily: HN, fontSize: "11px", letterSpacing: "0.22em", textTransform: "uppercase",
                    color: "rgba(245,243,239,0.45)", textDecoration: "none",
                  }}
                >Area soci</Link>
              )}
              <button
                onClick={handleLogout}
                style={{
                  background: "none", border: "none", cursor: "pointer",
                  fontFamily: HN, fontSize: "11px", letterSpacing: "0.22em", textTransform: "uppercase",
                  color: "rgba(245,243,239,0.3)",
                }}
              >Logout</button>
            </div>
          ) : (
            <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
              <Link
                href="/login"
                onClick={() => setMenuOpen(false)}
                style={{
                  fontFamily: HN, fontSize: "11px", letterSpacing: "0.22em", textTransform: "uppercase",
                  color: "rgba(245,243,239,0.55)", textDecoration: "none",
                }}
              >Area soci</Link>
              <button
                onClick={() => { setMenuOpen(false); setLoginOpen(true) }}
                style={{
                  background: "none", border: "none", cursor: "pointer",
                  fontFamily: HN, fontSize: "9px", letterSpacing: "0.18em", textTransform: "uppercase",
                  color: "rgba(245,243,239,0.2)",
                }}
              >Staff</button>
            </div>
          )}
        </div>
      )}

      <LoginModal open={loginOpen} onOpenChange={setLoginOpen} hideTrigger />
    </>
  )
}
