'use client'

import React, { useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { sendNewsLetterRequest } from '@/services/newsLetter'
export  function Newsletter() {
  const [emailNewsLetter, setEmailNewsLetter] = useState('')
  const [status, setStatus] = useState({ type: '', message: '' })
  const [loading, setLoading] = useState(false)

  const handleNewsletter = async (e) => {
    e.preventDefault()
    setLoading(true)
    setStatus({ type: '', message: '' })

    try {
      const { success, message } = await sendNewsLetterRequest({ email: emailNewsLetter })

      if (success) {

        setStatus({
          type: 'success',
          message: message
        })
        setEmailNewsLetter('')
      }
      else {
        setStatus({
          type: 'error',
          message: message
        })
      }
} catch (error) {
      setStatus({
        type: 'error',
        message: error.message || 'Si è verificato un errore durante l\'iscrizione'
      })
    } finally {
      setLoading(false)
    }
  }

  return (
      <div className="container mx-auto px-4">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-4xl font-bold mb-8 text-orange-500">Stay Connected</h2>
          <p className="text-lg mb-8 text-orange-200">
            Subscribe to our newsletter for exclusive updates and event announcements.
          </p>
          
          {status.message && (
            <Alert 
              className={`mb-6 ${
                status.type === 'success' 
                  ? 'bg-green-500/10 border-green-500/20' 
                  : 'bg-red-500/10 border-red-500/20'
              }`}
            >
              <AlertDescription className={`${
                status.type === 'success' ? 'text-green-400' : 'text-red-400'
              }`}>
                {status.message}
              </AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleNewsletter} className="flex gap-4 max-w-md mx-auto">
            <Input
              id="newsletter-email"  
              type="email"
              placeholder="Enter your email"
              value={emailNewsLetter}
              onChange={(e) => setEmailNewsLetter(e.target.value)}
              className="flex-1 bg-transparent border-orange-500 text-orange-200 placeholder:text-orange-200/50 focus:border-orange-400 focus-visible:ring-0 focus-visible:ring-offset-0"
              required
              disabled={loading}
              
            />
            <Button 
              type="submit" 
              className="bg-orange-500 hover:bg-orange-600 text-black px-3"
              disabled={loading}
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-black border-t-transparent" />
              ) : (
                <ArrowRight className="h-5 w-5" />
              )}
            </Button>
          </form>
        </div>
      </div>
   
  )
}