"use client"
import Image from "next/image"

import { useState, useEffect } from "react"
import { DialogTitle } from "@/components/ui/dialog"

import { motion } from "framer-motion"
import { Menu, LogOut, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger, SheetOverlay } from "@/components/ui/sheet"
import Link from "next/link"
import LoginModal from "@/components/auth/LoginModal"
import { useUser } from "@/contexts/userContext"
import { logout } from "@/config/firebase"
import { routes } from "@/config/routes"

export const Navigation = () => {
  const [isScrolled, setIsScrolled] = useState(false)
  const { user, isAdmin } = useUser()
  const [open, setOpen] = useState(false)
  const [loginOpen, setLoginOpen] = useState(false)

  const handleNavClick = () => setOpen(false)

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20)
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error("Logout error:", error)
    }
  }

  const profileLink = user ? (isAdmin ? routes.admin.dashboard : routes.user.profile) : null

  // Fondo gestito via CSS per avere un effetto "pill" più ricco
  const navBg = isScrolled ? "nav-shell--scrolled" : ""

  return (
    <motion.nav
      className="relative w-full z-50 transition-all duration-300 bg-transparent"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container px-4 mx-auto py-2">
        <Sheet open={open} onOpenChange={setOpen}>
          <div className="nav-mobile-bar lg:hidden">
            <Link href="/" className="nav-brand hover:opacity-80 transition-opacity">
              <Image
                src="/secondaryLogoWhite.png"
                alt="MCP Logo"
                width={72}
                height={52}
                className="h-auto"
                priority
              />
            </Link>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="nav-burger mb-3">
                <Menu className="h-6 w-6" />
              </Button>
            </SheetTrigger>
          </div>

          <div className={`nav-shell ${navBg} hidden lg:block`}>
            <div className="nav-shell__inner">
              {/* Logo */}
              <Link href="/" className="nav-brand hover:opacity-80 transition-opacity">
                <Image
                  src="/secondaryLogoWhite.png"
                  alt="MCP Logo"
                  width={86}
                  height={60}
                  className="h-auto"
                  priority
                />
              </Link>

              {/* Navbar links (desktop) */}
              <div className="nav-links hidden lg:flex">
                <NavLink href={routes.events.foto.gallery}>Photos</NavLink>
                <NavLink href={routes.events.allevents}>Events</NavLink>
                <NavLink href="/#about">About</NavLink>
                <NavLink href="/#contact-section">Contact</NavLink>
              </div>

              <div className="nav-actions hidden lg:flex">
                {user ? (
                  <>
                    {profileLink && (
                      <NavLink href={profileLink} compact>
                        <User className="h-4 w-4" />
                        {isAdmin ? "Admin" : "Profile"}
                      </NavLink>
                    )}
                    <Button variant="ghost" className="nav-action-btn" onClick={handleLogout}>
                      <LogOut className="h-4 w-4" />
                      Logout
                    </Button>
                  </>
                ) : (
                  <LoginModal />
                )}
              </div>
            </div>
          </div>

          <SheetOverlay className="fixed inset-0 bg-black/70 supports-[backdrop-filter]:backdrop-blur-md z-[190]" />

              <SheetContent side="right" className="z-[200] w-full sm:w-[380px] nav-drawer">
            <DialogTitle className="sr-only">Navigation Menu</DialogTitle>

                <div className="nav-drawer__header">
                  <Image src="/secondaryLogoWhite.png" alt="MCP Logo" width={84} height={60} priority />
                  <p className="nav-drawer__tagline">Culture • Events • Community</p>
                </div>

                <nav className="nav-drawer__links">
              <NavLink href={routes.events.foto.gallery} mobile onClick={handleNavClick}>
                Photos
              </NavLink>
              <NavLink href="/events" mobile onClick={handleNavClick}>
                Events
              </NavLink>
              <NavLink href="/#about" mobile onClick={handleNavClick}>
                About
              </NavLink>
              <NavLink href="/#join" mobile onClick={handleNavClick}>
                Join Us
              </NavLink>
              <NavLink href="/#contact-section" mobile onClick={handleNavClick}>
                Contact
              </NavLink>
            </nav>

            <div className="nav-drawer__footer">
              {user ? (
                <>
                  {profileLink && (
                    <NavLink href={profileLink} mobile>
                      <User className="h-5 w-5" />
                      {isAdmin ? "Admin" : "Profile"}
                    </NavLink>
                  )}
                  <Button variant="ghost" className="nav-drawer__action" onClick={handleLogout}>
                    <LogOut className="h-5 w-5" />
                    Logout
                  </Button>
                </>
              ) : (
                <Button
                  variant="ghost"
                  className="nav-drawer__action"
                  onClick={() => {
                    setOpen(false)
                    setLoginOpen(true)
                  }}
                >
                  LOGIN
                </Button>
              )}
            </div>
          </SheetContent>
        </Sheet>
      </div>
      {!user && <LoginModal open={loginOpen} onOpenChange={setLoginOpen} hideTrigger />}
    </motion.nav>
  )
}

const NavLink = ({ href, children, mobile, compact, onClick }) => (
  <Link
    href={href}
    onClick={onClick}
    className={`nav-link ${mobile ? "nav-link--mobile" : ""} ${compact ? "nav-link--compact" : ""}`}
  >
    <span className="relative z-10 flex items-center gap-2">{children}</span>
    <span className="nav-link__underline" />
  </Link>
)

export default Navigation
