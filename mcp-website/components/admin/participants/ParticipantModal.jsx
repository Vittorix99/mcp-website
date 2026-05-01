"use client"

import { useEffect, useMemo, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Button } from "@/components/ui/button"
import { useMediaQuery } from "@/hooks/useMediaQuery"
import { Loader2, X } from "lucide-react"
import { detectEmailTypo } from "@/lib/emailValidation"

const PAYMENT_METHOD_OPTIONS = [
  { value: "website", label: "Website" },
  { value: "private_paypal", label: "Private PayPal" },
  { value: "iban", label: "IBAN" },
  { value: "cash", label: "Cash" },
  { value: "omaggio", label: "Omaggio" },
]

export function ParticipantModal({
  isOpen,
  onClose,
  form = {},
  isEditMode = false,
  loading: externalLoading = false,
  membershipOptions = [],
  currentMembershipYear = new Date().getFullYear().toString(),
  membershipLoading = false,
  onSubmit,
  onInput,
  onCheckbox,
  onMemberSelect,
}) {
  const selectedMembershipId = form.membership_id ?? form.membershipId ?? null
  const isMember = !!selectedMembershipId
  const isMobile = !useMediaQuery("(min-width: 768px)")
  const defaultMembershipIncluded = !!form.membership_included
  const defaultSendTicket = !!form.send_ticket_on_create
  const emailTypo = detectEmailTypo(form.email || "")

  const [internalLoading, setInternalLoading] = useState(false)
  const [membershipSearch, setMembershipSearch] = useState("")

  const handleSubmit = async (e) => {
    e.preventDefault()
    setInternalLoading(true)
    await onSubmit(e)
    setInternalLoading(false)
  }

  const isLoading = internalLoading || externalLoading
  const filteredMemberships = useMemo(() => {
    const q = membershipSearch.trim().toLowerCase()
    const base = Array.isArray(membershipOptions) ? membershipOptions : []
    const result = q
      ? base.filter((m) => `${m.name} ${m.surname} ${m.email} ${m.id}`.toLowerCase().includes(q))
      : base
    return result.slice(0, 100)
  }, [membershipOptions, membershipSearch])

  const selectedMembership = useMemo(
    () => (Array.isArray(membershipOptions) ? membershipOptions.find((m) => m.id === selectedMembershipId) : null) || null,
    [membershipOptions, selectedMembershipId]
  )

  const membershipSelectOptions = useMemo(() => {
    const map = new Map()
    if (selectedMembership) map.set(selectedMembership.id, selectedMembership)
    filteredMemberships.forEach((m) => map.set(m.id, m))
    return Array.from(map.values())
  }, [selectedMembership, filteredMemberships])

  useEffect(() => {
    if (!isOpen) setMembershipSearch("")
  }, [isOpen])

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
      {/* ── Selezione membro esistente (solo creazione) ── */}
      {!isEditMode && (
        <div className="rounded-lg border border-zinc-700 p-3 bg-zinc-900/40 space-y-2">
          <Label className="text-sm font-semibold text-zinc-300">
            Collega a membro esistente <span className="text-zinc-500 font-normal">(opzionale — pre-compila i campi)</span>
          </Label>

          {isMember ? (
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm text-green-400 border border-green-700 bg-green-950 px-3 py-1 rounded">
                {selectedMembership
                  ? `${selectedMembership.name} ${selectedMembership.surname}`.trim()
                  : selectedMembershipId}
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onMemberSelect && onMemberSelect(null)}
              >
                Rimuovi
              </Button>
            </div>
          ) : (
            <>
              <Input
                placeholder={`Cerca per nome, cognome o email…`}
                value={membershipSearch}
                onChange={(e) => setMembershipSearch(e.target.value)}
                disabled={membershipLoading}
              />
              {membershipSearch.trim() && (
                <select
                  size={Math.min(membershipSelectOptions.length + 1, 6)}
                  className="w-full rounded border border-zinc-700 bg-zinc-800 p-2 text-white text-sm"
                  disabled={membershipLoading || !membershipSelectOptions.length}
                  onChange={(e) => {
                    if (!e.target.value) return
                    const member = membershipOptions.find((m) => m.id === e.target.value)
                    if (member && onMemberSelect) {
                      onMemberSelect(member)
                      setMembershipSearch("")
                    }
                  }}
                  defaultValue=""
                >
                  <option value="" disabled>Seleziona membro…</option>
                  {membershipSelectOptions.map((m) => (
                    <option key={m.id} value={m.id}>
                      {`${m.surname || ""} ${m.name || ""}`.trim() || m.id}
                      {m.email ? ` · ${m.email}` : ""}
                    </option>
                  ))}
                  {membershipSelectOptions.length === 0 && (
                    <option value="" disabled>Nessun risultato</option>
                  )}
                </select>
              )}
            </>
          )}
        </div>
      )}

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
        {emailTypo && (
          <p className="mt-1 text-xs text-amber-400">
            Hai scritto '{emailTypo.typedDomain}'. Intendevi '{emailTypo.suggestedDomain}'?
          </p>
        )}
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

      <div>
        <Label htmlFor="payment_method">Metodo di pagamento</Label>
        <select
          id="payment_method"
          name="payment_method"
          value={form.payment_method || ""}
          onChange={onInput}
          className="w-full mt-1 rounded border border-zinc-700 bg-zinc-800 p-2 text-white"
        >
          <option value="">Seleziona metodo</option>
          {PAYMENT_METHOD_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {isEditMode && (
        <div className="space-y-2 rounded-lg border border-zinc-700 p-3 bg-zinc-900/40">
          <div className="flex items-center justify-between">
            <Label className="text-sm">Associazione membership ({currentMembershipYear})</Label>
            {isMember && (
              <span className="text-xs text-green-400">
                {selectedMembership ? `${selectedMembership.name} ${selectedMembership.surname}`.trim() : selectedMembershipId}
              </span>
            )}
          </div>
          <Input
            placeholder={`Cerca membro ${currentMembershipYear}...`}
            value={membershipSearch}
            onChange={(e) => setMembershipSearch(e.target.value)}
            disabled={membershipLoading}
          />
          <select
            value={selectedMembershipId || ""}
            onChange={(e) => onInput({ target: { name: "membership_id", value: e.target.value || null } })}
            className="w-full mt-1 rounded border border-zinc-700 bg-zinc-800 p-2 text-white"
            disabled={membershipLoading || !membershipSelectOptions.length}
          >
            <option value="">Nessuna membership</option>
            {membershipSelectOptions.map((m) => (
              <option key={m.id} value={m.id}>
                {`${m.surname || ""} ${m.name || ""}`.trim() || m.id} {m.email ? `· ${m.email}` : ""}
              </option>
            ))}
          </select>
          {isMember && (
            <Button
              type="button"
              variant="outline"
              onClick={() => onInput({ target: { name: "membership_id", value: null } })}
              className="w-full"
            >
              Rimuovi associazione membership
            </Button>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 pt-2">
  {!isEditMode && (
    <>
      {!isMember && (
        <div className="flex items-center gap-2">
          <Checkbox
            id="membership_included"
            name="membership_included"
            checked={defaultMembershipIncluded}
            onCheckedChange={(val) => onCheckbox("membership_included", val)}
          />
          <Label htmlFor="membership_included">Includi tesseramento</Label>
        </div>
      )}
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
  <div className="flex items-center gap-2">
    <Checkbox
      id="riduzione"
      name="riduzione"
      checked={!!form.riduzione}
      onCheckedChange={(val) => onCheckbox("riduzione", val)}
    />
    <Label htmlFor="riduzione">Riduzione (ha pagato meno)</Label>
  </div>
  {isEditMode && isMember && (
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
