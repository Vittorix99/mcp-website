"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function WaitlistModal({ isOpen, onOpenChange, eventId, eventTitle }) {
  const [waitlistForm, setWaitlistForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitSuccess, setSubmitSuccess] = useState(false)

  const handleWaitlistInputChange = (e) => {
    const { name, value } = e.target
    setWaitlistForm((prev) => ({
      ...prev,
      [name]: value,
    }))
  }

  const handleWaitlistSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Chiamata alla funzione joinwaitlistevent con i dati del form e l'ID dell'evento
      await joinwaitlistevent({
        ...waitlistForm,
        eventId,
      })

      setSubmitSuccess(true)
      // Reset del form dopo 3 secondi e chiusura della modale
      setTimeout(() => {
        setWaitlistForm({
          firstName: "",
          lastName: "",
          email: "",
          phone: "",
        })
        setSubmitSuccess(false)
        onOpenChange(false)
      }, 3000)
    } catch (error) {
      console.error("Error joining waitlist:", error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="bg-black border border-mcp-orange/50 text-white max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl md:text-2xl font-bold gradient-text">Join the wait list</DialogTitle>
          <DialogDescription className="text-sm md:text-base text-gray-300">
            Fill out the form below to join the wait list for {eventTitle ? `"${eventTitle}"` : "this exclusive event"}.
          </DialogDescription>
        </DialogHeader>

        {submitSuccess ? (
          <div className="py-6 text-center">
            <div className="text-green-500 text-lg font-bold mb-2">Success!</div>
            <p className="text-gray-300">
              You've been added to the wait list. We'll contact you if a spot becomes available.
            </p>
          </div>
        ) : (
          <form onSubmit={handleWaitlistSubmit} className="space-y-4 mt-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="firstName" className="text-sm text-gray-300">
                  First Name
                </Label>
                <Input
                  id="firstName"
                  name="firstName"
                  value={waitlistForm.firstName}
                  onChange={handleWaitlistInputChange}
                  required
                  className="bg-black/30 border-mcp-orange/50 text-white"
                />
              </div>
              <div>
                <Label htmlFor="lastName" className="text-sm text-gray-300">
                  Last Name
                </Label>
                <Input
                  id="lastName"
                  name="lastName"
                  value={waitlistForm.lastName}
                  onChange={handleWaitlistInputChange}
                  required
                  className="bg-black/30 border-mcp-orange/50 text-white"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="email" className="text-sm text-gray-300">
                Email
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={waitlistForm.email}
                onChange={handleWaitlistInputChange}
                required
                className="bg-black/30 border-mcp-orange/50 text-white"
              />
            </div>
            <div>
              <Label htmlFor="phone" className="text-sm text-gray-300">
                Phone Number
              </Label>
              <Input
                id="phone"
                name="phone"
                type="tel"
                value={waitlistForm.phone}
                onChange={handleWaitlistInputChange}
                required
                className="bg-black/30 border-mcp-orange/50 text-white"
              />
            </div>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-mcp-gradient hover:opacity-90 text-white font-bold py-2 text-sm md:text-base h-10 rounded-md transition-all duration-300"
            >
              {isSubmitting ? "Submitting..." : "Submit"}
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}

// Funzione temporanea per la lista d'attesa - da sostituire con l'implementazione reale
async function joinwaitlistevent(data) {
  // Simulazione di una chiamata API
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ success: true })
    }, 1500)
  })
}

