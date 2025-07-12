"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { useMediaQuery } from "@/hooks/useMediaQuery"
import { Loader2, X } from "lucide-react"

export function ParticipantModal({
  isOpen,
  onClose,
  form = {},
  isEditMode = false,
  loading: externalLoading = false,
  onSubmit,
  onInput,
  onCheckbox,
}) {
  const isMember = !!form.membershipId
  const isMobile = !useMediaQuery("(min-width: 768px)")
  const defaultMembershipIncluded = !!form.membership_included
  const defaultSendTicket = !!form.send_ticket_on_create

  const [internalLoading, setInternalLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setInternalLoading(true)
    await onSubmit(e)
    setInternalLoading(false)
  }

  const isLoading = internalLoading || externalLoading

  const handleBirthdateChange = (value) => {
    const cleaned = value.replace(/\D/g, "")
    let formatted = cleaned
    if (cleaned.length > 4) {
      formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2, 4)}-${cleaned.slice(4, 8)}`
    } else if (cleaned.length > 2) {
      formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2)}`
    }
    onInput({ target: { name: "birthdate", value: formatted } })
  }

  const renderFields = () => (
    <>
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="name">Nome</Label>
          <Input id="name" name="name" value={form.name || ""} onChange={onInput} required />
        </div>
        <div>
          <Label htmlFor="surname">Cognome</Label>
          <Input id="surname" name="surname" value={form.surname || ""} onChange={onInput} required />
        </div>
      </div>

      <div>
        <Label htmlFor="email">Email</Label>
        <Input id="email" name="email" type="email" value={form.email || ""} onChange={onInput} required />
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="phone">Telefono</Label>
          <Input id="phone" name="phone" value={form.phone || ""} onChange={onInput} />
        </div>
        <div>
          <Label htmlFor="birthdate">Data di nascita</Label>
          <Input
            id="birthdate"
            name="birthdate"
            placeholder="DD-MM-YYYY"
            value={form.birthdate || ""}
            onChange={(e) => handleBirthdateChange(e.target.value)}
          />
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <Label htmlFor="gender">Genere</Label>
          {isMobile ? (
            <Input
              id="gender"
              name="gender"
              value={form.gender || ""}
              placeholder="M o F"
              onChange={(e) => {
                const val = e.target.value.toUpperCase()
                const normalized = val === "M" ? "male" : val === "F" ? "female" : ""
                onInput({ target: { name: "gender", value: normalized } })
              }}
              className="w-full mt-1 rounded border border-zinc-700 bg-zinc-800 p-2 text-white"
            />
          ) : (
            <select
              id="gender"
              name="gender"
              value={form.gender || ""}
              onChange={onInput}
              className="w-full mt-1 rounded border border-zinc-700 bg-zinc-800 p-2 text-white"
            >
              <option value="">Seleziona genere</option>
              <option value="male">Maschio</option>
              <option value="female">Femmina</option>
            </select>
          )}
        </div>
        <div>
          <Label htmlFor="price">Prezzo (€)</Label>
          <Input id="price" name="price" type="number" value={form.price || ""} onChange={onInput} />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 pt-2">
  {!isEditMode && (
    <>
      <div className="flex items-center gap-2">
        <Checkbox
          id="membership_included"
          name="membership_included"
          checked={defaultMembershipIncluded}
          onCheckedChange={(val) => onCheckbox("membership_included", val)}
        />
        <Label htmlFor="membership_included">Tessera da includere</Label>
      </div>
      <div className="flex items-center gap-2">
        <Checkbox
          id="send_ticket_on_create"
          name="send_ticket_on_create"
          checked={defaultSendTicket}
          onCheckedChange={(val) => onCheckbox("send_ticket_on_create", val)}
        />
        <Label htmlFor="send_ticket_on_create">Invia biglietto al salvataggio</Label>
      </div>
      <div className="flex items-center gap-2">
        <Checkbox
          id="newsletterConsent"
          name="newsletterConsent"
          checked={!!form.newsletterConsent}
          onCheckedChange={(val) => onCheckbox("newsletterConsent", val)}
        />
        <Label htmlFor="newsletterConsent">Acconsente alla newsletter</Label>
      </div>
    </>
  )}
  {isMember && (
    <div className="text-sm text-green-400 border border-green-600 bg-green-950 px-3 py-1 rounded">
      Già tesserato
    </div>
  )}
</div>


    </>
  )

  const renderFooter = () => (
    <div className="flex justify-end gap-2 pt-4 mr-6">
      <Button type="button" variant="outline" onClick={onClose}>
        Annulla
      </Button>
      <Button type="submit" disabled={isLoading} className="h-12 px-6 text-base font-semibold">
        {isLoading ? (
          <span className="flex items-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin" /> Salvataggio...
          </span>
        ) : isEditMode ? "Aggiorna" : "Crea"}
      </Button>
    </div>
  )

  if (isMobile && isOpen) {
    return (
    <div className="fixed inset-0 z-50 bg-black no-nav">
  <form onSubmit={handleSubmit} className="flex flex-col h-full">
    <div className="flex items-center justify-between p-4 border-b border-gray-700 shrink-0">
      <h2 className="text-xl font-bold">{isEditMode ? "Modifica" : "Nuovo"} Evento</h2>
      <Button variant="ghost" size="icon" onClick={onClose}>
        <X className="h-5 w-5 text-white" />
      </Button>
    </div>

    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {renderFields()}
    </div>

    <div className="border-t border-gray-700 p-4 shrink-0">
      {renderFooter()}
    </div>
  </form>
</div>
    )
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] bg-black border-mcp-orange/50 rounded-xl">
        <DialogHeader>
          <DialogTitle className="text-center text-2xl gradient-text">
            {isEditMode ? "Modifica partecipante" : "Nuovo partecipante"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          {renderFields()}
          {renderFooter()}
        </form>
      </DialogContent>
    </Dialog>
  )
}