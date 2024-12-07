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
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
      isScrolled ? 'bg-black/80 backdrop-blur-md' : 'bg-transparent'
    }`}>
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-orange-500 hover:text-orange-400 transition-colors">
          MCP
        </Link>
        <div className="hidden md:flex items-center space-x-6">
          <Link href="/#about" className="text-orange-200 hover:text-orange-500 transition-colors text-sm uppercase tracking-wider">
            About
          </Link>
          <Link href="/#join" className="text-orange-200 hover:text-orange-500 transition-colors text-sm uppercase tracking-wider">
            Join Us
          </Link>
          <Link href="/#contact" className="text-orange-200 hover:text-orange-500 transition-colors text-sm uppercase tracking-wider">
            Contact
          </Link>
          {isAuthenticated ? (
            <Link href="/profile" className="text-orange-200 hover:text-orange-500 transition-colors text-sm uppercase tracking-wider">
              Profile
            </Link>
          ) : (
            <div className="flex items-center">
              <LoginModal />
            </div>
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
              <Link href="/#about" className="text-orange-200 hover:text-orange-500 transition-colors text-lg">
                About
              </Link>
              <Link href="/#join" className="text-orange-200 hover:text-orange-500 transition-colors text-lg">
                Join Us
              </Link>
              <Link href="/#contact" className="text-orange-200 hover:text-orange-500 transition-colors text-lg">
                Contact
              </Link>
              {isAuthenticated ? (
                <Link href="/profile" className="text-lg hover:text-orange-500 transition-colors">
                  Profile
                </Link>
              ) : (
                <div className="flex items-center">
                  <LoginModal />
                </div>
              )}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  )
}

