"use client"

import React, { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import Link from "next/link"

export const Navigation = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // This is a placeholder for actual authentication check
    // Replace this with your actual authentication logic
    const checkAuth = async () => {
      // Simulating an API call or checking local storage
      const auth = localStorage.getItem('isAuthenticated') === 'true'
      setIsAuthenticated(auth)
    }
    checkAuth()
  }, [])

  const handleLogin = () => {
    // Placeholder for login logic
    console.log('Login clicked')
    // Implement your login logic here
  }

  return (
<nav className="fixed top-0 left-0 right-0 z-50 bg-black/50 backdrop-blur-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-orange-500">MCP</Link>
        <div className="hidden md:flex space-x-6">
          <Link href="/#about" className="text-orange-200 hover:text-orange-500 transition-colors">About</Link>
          <Link href="/#join" className="text-orange-200 hover:text-orange-500 transition-colors">Join Us</Link>
          <Link href="/#contact" className="text-orange-200 hover:text-orange-500 transition-colors">Contact</Link>
          {isAuthenticated ? (
            <Link href="/profile" className="text-orange-200 hover:text-orange-500 transition-colors ">Profile</Link>
          ) : (
            <Button 
              variant="ghost" 
              className="text-orange-200 hover:text-orange-500 transition-colors px-3 py-0 h-auto font-normal"
              onClick={handleLogin}
            >
              Login
            </Button>
          )}
        </div>
        <Sheet>
          <SheetTrigger asChild>
            <Button variant="ghost" size="icon" className="md:hidden text-orange-500">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="bg-black text-orange-200">
            <nav className="flex flex-col space-y-4 mt-8">
              <Link href="/#about" className="text-lg hover:text-orange-500 transition-colors">About</Link>
              <Link href="/#join" className="text-lg hover:text-orange-500 transition-colors">Join Us</Link>
              <Link href="/#contact" className="text-lg hover:text-orange-500 transition-colors">Contact</Link>
              {isAuthenticated ? (
                <Link href="/profile" className="text-lg hover:text-orange-500 transition-colors">Profile</Link>
              ) : (
                <Button variant="ghost" className="text-lg text-left hover:text-orange-500 transition-colors" onClick={handleLogin}>
                  Login
                </Button>
              )}
            </nav>
          </SheetContent>
        </Sheet>
      </div>
    </nav>
  )
}

export default Navigation