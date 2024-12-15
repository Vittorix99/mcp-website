'use client'

import React from 'react'
import { Contact, Menu } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import Image from "next/image"
import Link from "next/link"
import { useRouter } from 'next/navigation'
import {LoginModal} from "@/components/auth/LoginModal" 
import {ContactUs} from "@/components/pages/ContactUs"

const AnimatedBackground = () => (
  <div className="fixed inset-0 z-0 opacity-20">
    <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <pattern id="lines" width="100" height="100" patternUnits="userSpaceOnUse">
          <path d="M0,50 Q25,25 50,50 T100,50" fill="none" stroke="rgba(249, 115, 22, 0.5)" strokeWidth="2">
            <animate attributeName="d" from="M0,50 Q25,0 50,50 T100,50" to="M0,50 Q25,100 50,50 T100,50" dur="10s" repeatCount="indefinite" />
          </path>
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#lines)" />
    </svg>
  </div>
)


const MembershipForm = ({ onClose }) => {
  const handleSubmit = (e) => {
    e.preventDefault()
    // Handle form submission here
    onClose()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <Label htmlFor="name" className="text-orange-200">Full Name</Label>
        <Input id="name" type="text" required className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" />
      </div>
      <div>
        <Label htmlFor="email" className="text-orange-200">Email</Label>
        <Input id="email" type="email" required className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" />
      </div>
      <div>
        <Label htmlFor="birthdate" className="text-orange-200">Date of Birth</Label>
        <Input id="birthdate" type="date" required className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" />
      </div>
      <Button type="submit" className="w-full bg-orange-500 hover:bg-orange-600 text-black">
        Join the Association
      </Button>
    </form>
  )
}


export default function LandingPage() {
const router = useRouter()
  const goToSubscribe = () => {
      router.push('/subscribe')
  }


  return (
    <div className="min-h-screen bg-black text-orange-200">


      {/* Hero Section */}
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        <div className="relative z-10 text-center px-4">
          <h1 className="text-6xl md:text-8xl font-bold mb-6 text-orange-500">
            MUSIC CONNECTING PEOPLE
          </h1>
          <p className="text-xl md:text-2xl mb-8">
            Experience the rhythm. Connect with the community.
          </p>
          <Button 
            size="lg" 
            className="bg-orange-500 hover:bg-orange-600 text-black"
            onClick={() => {
              document.getElementById('join').scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Join Our Cultural Association
          </Button>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-24 bg-black/50 backdrop-blur-md">
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

  
      <section id="join" className="relative py-24 bg-black">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-8 text-orange-500">Join Our Cultural Association</h2>
          <p className="text-lg mb-8">Become a part of our community and experience the power of music connection.</p>
          <Button 
            size="lg" 
            className="bg-orange-500 hover:bg-orange-600 text-black"
            onClick={goToSubscribe}
          >
           Sign Up
          </Button>
        </div>
      </section>

      <section id="contact-section" className="relative py-24 bg-black">
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