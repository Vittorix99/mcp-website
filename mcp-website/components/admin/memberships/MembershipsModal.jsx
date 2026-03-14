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
  const defaultSendCard = form.send_card_on_create === true
  const defaultCreateWallet = form.create_wallet_on_create !== false
  const defaultSubscriptionValid = form.subscription_valid ?? true
  const startDateValue = (() => {
    if (!form.start_date) return ""
    const parsed = new Date(form.start_date)
    if (Number.isNaN(parsed.getTime())) return form.start_date
    return parsed.toISOString().slice(0, 10)
  })()

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
            <div className="space-y-2 pt-2">
              <div className="flex items-center gap-2">
                <Checkbox
                  id="create_wallet_on_create"
                  checked={defaultCreateWallet}
                  onCheckedChange={(val) => onCheckbox("create_wallet_on_create", val === true)}
                />
                <Label htmlFor="create_wallet_on_create">Crea tessera wallet (Pass2U)</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox
                  id="send_card_on_create"
                  name="send_card_on_create"
                  checked={defaultSendCard}
                  onCheckedChange={(val) => onCheckbox("send_card_on_create", val === true)}
                />
                <Label htmlFor="send_card_on_create">Invia tessera al salvataggio</Label>
              </div>
            </div>
          )}

          {isEditMode && (
            <>
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div>
                  <Label htmlFor="start_date">Data iscrizione</Label>
                  <Input
                    id="start_date"
                    name="start_date"
                    type="date"
                    value={startDateValue}
                    onChange={onInput}
                  />
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <Checkbox
                    id="subscription_valid"
                    name="subscription_valid"
                    checked={defaultSubscriptionValid}
                    onCheckedChange={(val) => onCheckbox("subscription_valid", val)}
                  />
                  <Label htmlFor="subscription_valid">Tessera valida</Label>
                </div>
              </div>
            </>
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
