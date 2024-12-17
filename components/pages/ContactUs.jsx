'use client'

import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import toast from 'react-hot-toast' // Importa react-hot-toast
import { sendContactRequest } from '@/services/contactService' // Import the service

export function ContactUs() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      await sendContactRequest({ name, email, message }) // Use the service
      toast.success("Your message has been sent successfully!") // Mostra un toast di successo
      setName('')
      setEmail('')
      setMessage('')
    } catch (error) {
      console.error('Error:', error.message)
      toast.error(error.message || "Failed to send message. Please try again.") // Mostra un toast di errore
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <h2 className="text-3xl font-bold text-center text-orange-200 mb-6">Contact Us</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="contact-name" className="text-orange-200">Name</Label>
          <Input 
            id="contact-name" 
            type="text" 
            required 
            className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" 
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="contact-email" className="text-orange-200">Email</Label>
          <Input 
            id="contact-email" 
            type="email" 
            required 
            className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="contact-message" className="text-orange-200">Message</Label>
          <Textarea 
            id="contact-message" 
            required 
            className="bg-black border-orange-500 text-orange-200 placeholder-orange-200/50" 
            rows={4} 
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
        </div>
        <Button 
          type="submit" 
          className="w-full bg-orange-500 hover:bg-orange-600 text-black"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Sending...' : 'Send Message'}
        </Button>
      </form>
    </div>
  )
}