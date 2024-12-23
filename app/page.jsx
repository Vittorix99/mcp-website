'use client'

import React, { useState } from 'react'
import { Menu, ArrowRight } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent } from "@/components/ui/card"
import Image from "next/image"
import Link from "next/link"
import { useRouter } from 'next/navigation'
import { ContactUs} from '@/components/pages/ContactUs'
import { LogoSection } from '@/components/pages/Logo'
import { NextEventSection } from '@/components/pages/NextEventSection'
import { Newsletter } from '@/components/pages/NewsLetter'



export default function LandingPage() {
  const router = useRouter()


  return (
    <div className="min-h-screen bg-black text-orange-200">

      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        <LogoSection />
  
      </section>

      {/* Next Event Section */}
      <section className="py-24 bg-black/50 backdrop-blur-md">
      <NextEventSection />
      
      </section>

      {/* About Section */}
      <section id="about" className="py-24 bg-black">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl font-bold mb-8 text-center text-orange-500">Our Philosophy</h2>
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-lg mb-6">
              Music Connecting People was born to find a safe, emotionally immersive, sonorously & visually stunning way of partying.
            </p>
            <p className="text-lg mb-6">
              We believe that through music, it is possible to reconnect with our inner essence and share it in real life. Electronic music offers not only the best journey when celebrating but also a way of self-reconciliation and embracing new horizons.
            </p>
            <p className="text-lg">
              We are drawn toward the future, while finding a guide in the past, lost in the present. Our future represents a fully committed goal of innovation and sustainability, the past the underground sounds that represent electronic music, and the present the total devotion to feelings, emotions, and connections.
            </p>
          </div>
        </div>
      </section>

      {/* Join Us Section */}
      <section id="join" className="py-24 bg-black/50 backdrop-blur-md">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-8 text-orange-500">Join Our Community</h2>
          <p className="text-lg mb-8">Become a part of our movement and experience the power of music connection.</p>
          <Link href="/subscribe">
            <Button size="lg" className="bg-orange-500 hover:bg-orange-600 text-black">
              Sign Up Now
            </Button>
          </Link>
        </div>
      </section>

      {/* Newsletter Section */}
      <section id="newsletter-section" className="relative py-24">
        <Newsletter/>
      </section>

      {/* Contact Section */}
      <section id="contact-section" className="py-24 bg-black/50 backdrop-blur-md">
              <ContactUs />
      </section>

      {/* Footer */}
      <footer className="bg-black text-orange-200 py-8">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; {new Date().getFullYear()} Music Connecting People. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}