"use client"

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"

export function MembershipModal({
  isOpen,
  onClose,
  form = {},
  isEditMode = false,
  loading = false,
  onSubmit,
  onInput,
  onCheckbox,
}) {
  const defaultSendCard = !!form.send_card_on_create

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-center">
            {isEditMode ? "Modifica membro" : "Nuovo membro"}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={onSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">Nome</Label>
              <Input
                id="name"
                name="name"
                value={form.name || ""}
                onChange={onInput}
                required
              />
            </div>
            <div>
              <Label htmlFor="surname">Cognome</Label>
              <Input
                id="surname"
                name="surname"
                value={form.surname || ""}
                onChange={onInput}
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              value={form.email || ""}
              onChange={onInput}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="phone">Telefono</Label>
              <Input
                id="phone"
                name="phone"
                value={form.phone || ""}
                onChange={onInput}
              />
            </div>
            <div>
              <Label htmlFor="birthdate">Data di nascita</Label>
              <Input
                id="birthdate"
                name="birthdate"
                placeholder="DD-MM-YYYY"
                value={form.birthdate || ""}
                onChange={onInput}
              />
            </div>
          </div>

          {!isEditMode && (
            <div className="flex items-center gap-2 pt-2">
              <Checkbox
                id="send_card_on_create"
                name="send_card_on_create"
                checked={defaultSendCard}
                onCheckedChange={(val) => onCheckbox("send_card_on_create", val)}
              />
              <Label htmlFor="send_card_on_create">Invia tessera al salvataggio</Label>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Annulla
            </Button>
            <Button type="submit" disabled={loading}>
              {isEditMode ? "Aggiorna" : "Crea"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}