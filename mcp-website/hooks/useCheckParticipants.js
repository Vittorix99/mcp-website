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
      const isValid = result?.valid === true

      if (!result || !isValid) {
        const errs = Array.isArray(result?.errors)
          ? result.errors
          : Array.isArray(result?.messages)
            ? result.messages
            : [result?.message || result?.error || "Errore di validazione partecipanti."]
        setErrors(errs)
        return { valid: false, errors: errs }
      }

      // Se valido, ritorniamo l'intero payload (può contenere nonMembers, members, ecc.)
      return result
    } catch (err) {
      console.error("Errore durante checkParticipants:", err)
      const errs = ["Errore di rete. Riprova."]
      setErrors(errs)
      return { valid: false, errors: errs }
    } finally {
      setLoading(false)
    }
  }

  return { checkParticipants, loading, errors }
}
