'use client'

import React, { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import Link from "next/link"
import LoginModal from '../auth/LoginModal'

export const Navigation = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    const checkAuth = async () => {
      // This is a placeholder for actual authentication check
      // Replace this with your actual authentication logic
      const auth = localStorage.getItem('isAuthenticated') === 'true'
      setIsAuthenticated(auth)
    }
    checkAuth()
  }, [])

  
  return (
    <nav
    className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled ? 'bg-black/80 backdrop-blur-md' : 'bg-transparent'
    }`}
  >
    <div className="container px-4 mx-auto py-4 flex justify-between items-center">
      {/* Logo */}
      <Link href="/" className="text-2xl mw-auto font-bold text-orange-500 hover:text-orange-400 transition-colors">
        MCP
      </Link>
      
      {/* Navbar links */}
      <div className="flex items-center space-x-6 lg:ml-auto ml-auto hidden md:flex">
        <NavLink href="/#about">About</NavLink>
        <NavLink href="/#join">Join Us</NavLink>
        <NavLink href="/#contact">Contact</NavLink>
        {isAuthenticated ? (
          <NavLink href="/profile">Profile</NavLink>
        ) : (
          <LoginModal />
        )}
      </div>
      <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden text-orange-500 hover:text-orange-400">
              <Menu className="h-6 w-6" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[300px] bg-black/95 border-orange-500/20">
            <nav className="flex flex-col space-y-6 mt-12">
              <NavLink href="/#about" mobile>About</NavLink>
              <NavLink href="/#join" mobile>Join Us</NavLink>
              <NavLink href="/#contact" mobile>Contact</NavLink>
              {isAuthenticated ? (
                <NavLink href="/profile" mobile>Profile</NavLink>
              ) : (
                <LoginModal />
              )}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  )
}

const NavLink = ({ href, children, mobile }) => (
  <Link 
    href={href} 
    className={`relative text-orange-200 hover:text-orange-500 transition-all duration-300 ${
      mobile ? 'text-lg' : 'text-sm uppercase tracking-wider'
    } group inline-block`}
  >
    <span className="relative z-10">{children}</span>
    <span className="absolute inset-x-0 bottom-0 h-0.5 bg-orange-500 transform origin-left scale-x-0 transition-transform duration-300 group-hover:scale-x-100" />
  </Link>
)
export default Navigation
