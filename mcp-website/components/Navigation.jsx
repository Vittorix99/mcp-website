"use client"
import Image from "next/image"

import { useState, useEffect } from "react"
import { DialogTitle } from "@/components/ui/dialog"


import { motion } from "framer-motion"
import { Menu, LogOut, User, Calendar, Image as ImageIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import Link from "next/link"
import LoginModal from "@/components/auth/LoginModal"
import { useUser } from "@/contexts/userContext"
import { logout } from "@/config/firebase"
import { useRouter } from "next/navigation"
import { routes } from "@/config/routes"


export const Navigation = () => {
  const [isScrolled, setIsScrolled] = useState(false)
  const { user, isAdmin } = useUser()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const handleNavClick = () => {
    setOpen(false)
  }


  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }

    window.addEventListener("scroll", handleScroll)
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

  return (
    <motion.nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? "bg-black/80 backdrop-blur-md" : "bg-transparent"
      }`}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="container px-4 mx-auto py-4 flex justify-between items-center">
        {/* Logo */}
        <Link href="/" className="text-2xl font-bold gradient-text hover:opacity-80 transition-opacity">
              <Image src="/secondaryLogoWhite.png" alt="MCP Logo" width={80} height={60} className="h-auto" />

        </Link>

        {/* Navbar links */}
        <div className="flex items-center space-x-6 lg:ml-auto ml-auto hidden md:flex">
        {/*  <NavLink href="/#about">About</NavLink>
          <NavLink href="/#join">Join Us</NavLink>
          <NavLink href="/#contact-section">Contact</NavLink>}*/}
          <NavLink href={routes.events.foto.gallery}>
          <ImageIcon className="mr-2 h-4 w-4" />
          Photos
        </NavLink>
          <NavLink href={routes.events.allevents}>
            <Calendar className="mr-2 h-4 w-4" />
            Events
          </NavLink>
          {user ? (
            <>
              {profileLink && (
                <NavLink href={profileLink}>
                  <User className="mr-2 h-4 w-4" />
                  {isAdmin ? "Admin" : "Profile"}
                </NavLink>
              )}
              <Button
                variant="ghost"
                className="text-white hover:text-mcp-orange text-sm uppercase tracking-wider flex items-center"
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                LOGOUT
              </Button>
            </>
          ) : (
            <LoginModal />
          )}
        </div>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden text-white hover:text-mcp-orange">
              <Menu className="h-6 w-6" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[300px] bg-black/95 border-mcp-orange/20">
          <DialogTitle className="sr-only">Navigation Menu</DialogTitle>
            <nav className="flex flex-col space-y-6 mt-12">
              <NavLink href="/#about" mobile onClick={handleNavClick}>
                About
              </NavLink>
              <NavLink href="/#join" mobile onClick={handleNavClick}>
                Join Us
              </NavLink>
              <NavLink href="/#contact-section" mobile onClick={handleNavClick}>
                Contact
              </NavLink>
              <NavLink href={routes.events.foto.gallery} mobile onClick={handleNavClick}>
          <ImageIcon className="mr-2 h-4 w-4" />
          Photos
        </NavLink>
              <NavLink href="/events" mobile onClick={handleNavClick}>
                <Calendar className="mr-2 h-4 w-4" />
                Events
              </NavLink>
              {user ? (
                <>
                  {profileLink && (
                    <NavLink href={profileLink} mobile>
                      <User className="mr-2 h-4 w-4" />
                      {user.isAdmin ? "ADMIN" : "PROFILE"}
                    </NavLink>
                  )}
                  <Button
                    variant="ghost"
                    className="text-white hover:text-mcp-orange text-lg flex items-center justify-start"
                    onClick={handleLogout}
                  >
                    <LogOut className="mr-2 h-5 w-5" />
                    Logout
                  </Button>
                </>
              ) : (
                <LoginModal />
              )}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </motion.nav>
  )
}
const NavLink = ({ href, children, mobile, onClick }) => (
  <Link
    href={href}
    onClick={onClick}
    className={`relative text-white hover:text-mcp-orange transition-all duration-300 ${
      mobile ? "text-lg" : "text-sm uppercase tracking-wider"
    } group inline-flex items-center`}
  >
    <span className="relative z-10 flex items-center gap-2">{children}</span>
    <motion.span
      className="absolute inset-x-0 bottom-0 h-0.5 bg-mcp-orange"
      initial={{ scaleX: 0 }}
      whileHover={{ scaleX: 1 }}
      transition={{ duration: 0.3 }}
    />
  </Link>
)
export default Navigation

