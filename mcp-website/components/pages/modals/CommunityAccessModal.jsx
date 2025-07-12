"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"
import { set } from "date-fns"

export function CommunityAccessModal({ isOpen, onOpenChange, eventId, eventTitle, isVerified, setIsVerified }) {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      // Simuliamo una chiamata API con un ritardo
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Durante lo sviluppo, accettiamo qualsiasi email come valida
      const mockResponse = {
        success: true,
        message: "Membership verified successfully!",
      }

      if (mockResponse.success) {
        toast.success("Accesso concesso!", {
          description: "Ora puoi acquistare i biglietti per questo evento.",
        })

        // Salviamo l'email verificata in localStorage per simulare una sessione
        //localStorage.setItem(`community_verified_${eventId}`, email)
        setIsVerified(true)
        onOpenChange(false)

        // Ricarica la pagina per mostrare le opzioni di acquisto
        //window.location.reload()
      } else {
        setError(mockResponse.message || "Unable to verify community membership. Please try again.")
      }
    } catch (err) {
      console.error("Error verifying membership:", err)
      setError("An error occurred. Please try again later.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="bg-black border border-mcp-orange/30 text-white sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-mcp-orange text-xl font-atlantico tracking-atlantico-wide">
            Accesso Community
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Inserisci la tua email registrata per accedere a questo evento.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-white">
              Indirizzo Email
            </Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tua@email.com"
              required
              className="bg-black/50 border-gray-700 text-white"
            />
            <p className="text-xs text-gray-400">
              La tua email verrà verificata con la lista dei membri della community.
            </p>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <div className="flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="border-gray-700 text-gray-300 hover:bg-gray-800"
            >
              Annulla
            </Button>
            <Button type="submit" disabled={loading} className="bg-mcp-orange hover:bg-mcp-orange/90 text-black">
              {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              {loading ? "Verifica in corso..." : "Continua"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
