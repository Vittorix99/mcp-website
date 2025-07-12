"use client"

import { useState } from "react"
import { checkParticipants as checkParticipantsService } from "@/services/eventsTicket"

export function useCheckParticipants() {
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState([])

  const checkParticipants = async (eventId, participants) => {
    setLoading(true)
    setErrors([])

    try {
      const result = await checkParticipantsService(eventId, participants)

      if (!result.valid) {
        // Ora usiamo direttamente gli errori provenienti dal backend
        setErrors(result.errors || ["Errore di validazione partecipanti."])
        return false
      }

      return true
    } catch (err) {
      console.error("Errore durante checkParticipants:", err)
      setErrors(["Errore di rete. Riprova."])
      return false
    } finally {
      setLoading(false)
    }
  }

  return { checkParticipants, loading, errors }
}