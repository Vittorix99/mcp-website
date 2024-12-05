'use client'

import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle } from 'lucide-react'
import Link from 'next/link'

export default function SubscribePage() {
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    // Here you would typically send the form data to your backend
    // For now, we'll just set isSubmitted to true
    setIsSubmitted(true)
  }

  return (
    <div className="min-h-screen bg-black text-orange-200 py-24">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-8 text-orange-500">Join MCP Cultural Association</h1>
        
        <Card className="max-w-2xl mx-auto bg-black/50 backdrop-blur-md border-orange-500">
          <CardHeader>
            <CardTitle className="text-2xl text-orange-500">Become a Member</CardTitle>
            <CardDescription className="text-orange-200">
              Join our community and experience the power of music connection.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-orange-400">Benefits of Joining:</h2>
              <ul className="list-disc list-inside space-y-2 text-orange-200">
                <li>Exclusive access to MCP events</li>
                <li>Networking opportunities with like-minded music enthusiasts</li>
                <li>Participate in workshops and masterclasses</li>
                <li>Contribute to the growth of the electronic music scene</li>
                <li>Be part of a supportive and inclusive community</li>
                {/* Add more benefits as they are defined */}
              </ul>
            </div>
            
            <div className="bg-orange-500/20 p-4 rounded-md flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-orange-500 mt-0.5" />
              <p className="text-sm">
                Membership is free of charge. However, please note that your request will be automatically rejected if you are not following our Instagram account: 
                <a href="https://www.instagram.com/musiconnectingpeople_" target="_blank" rel="noopener noreferrer" className="font-bold hover:underline"> @musicconnectingpeople_</a>
              </p>
            </div>

            {!isSubmitted ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="firstName" className="text-orange-200">First Name</Label>
                    <Input id="firstName" required className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" />
                  </div>
                  <div>
                    <Label htmlFor="lastName" className="text-orange-200">Last Name</Label>
                    <Input id="lastName" required className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" />
                  </div>
                </div>
                <div>
                  <Label htmlFor="email" className="text-orange-200">Email</Label>
                  <Input id="email" type="email" required className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" />
                </div>
                <div>
                  <Label htmlFor="instagram" className="text-orange-200">Instagram Account</Label>
                  <Input id="instagram" required className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" placeholder="@yourusername" />
                </div>
                <Button type="submit" className="w-full bg-orange-500 hover:bg-orange-600 text-black">
                  Submit Application
                </Button>
              </form>
            ) : (
              <div className="text-center space-y-4">
                <p className="text-lg font-semibold text-orange-400">Thank you for your application!</p>
                <p>Your request will be processed by the Music Connecting People team. We will be in touch soon.</p>
              </div>
            )}
          </CardContent>
          <CardFooter className="text-sm text-orange-200/70 justify-center">
            <Link href="/" className="hover:text-orange-500 transition-colors">
              Return to Home Page
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  )
}