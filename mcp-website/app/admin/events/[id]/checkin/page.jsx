"use client"

import { useEffect, useMemo, useState, useCallback } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { Loader2, ArrowLeft, Check, UserPlus, RefreshCw } from "lucide-react"
import {routes} from "@/config/routes"

import { useAdminEvents } from "@/hooks/useAdminEvents"
import { useAdminParticipants } from "@/hooks/useAdminParticipants"

function QuickAddDialog({ open, onOpenChange, onSubmit }) {
  const [form, setForm] = useState({ name: "", surname: "", email: "", birthdate: "" })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) setForm({ name: "", surname: "", email: "", birthdate: "" })
  }, [open])

  const handleBirthdateChange = (value) => {
    const cleaned = value.replace(/\D/g, "")
    let formatted = cleaned
    if (cleaned.length > 4) {
      formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2, 4)}-${cleaned.slice(4, 8)}`
    } else if (cleaned.length > 2) {
      formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2)}`
    }
    setForm((f) => ({ ...f, birthdate: formatted }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await onSubmit(form)
      onOpenChange(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Aggiunta rapida</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <Label>Nome</Label>
            <Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
          </div>
          <div>
            <Label>Cognome</Label>
            <Input value={form.surname} onChange={(e) => setForm((f) => ({ ...f, surname: e.target.value }))} required />
          </div>
          <div>
            <Label>Email</Label>
            <Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} required />
          </div>
          <div>
            <Label>Data di nascita (gg-mm-aaaa)</Label>
            <Input
              type="text"
              placeholder="es. 30-08-1999"
              value={form.birthdate}
              onChange={(e) => handleBirthdateChange(e.target.value)}
              pattern="^\d{2}-\d{2}-\d{4}$"
              inputMode="numeric"
              required
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
            <Button type="submit" disabled={saving}>
              {saving ? <span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin"/> Salva…</span> : "Salva"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function CheckinPage() {
  const router = useRouter()
  const params = useParams() || {}
  const eventId = Array.isArray(params.id) ? params.id[0] : params.id

  const { events, loading: evLoad } = useAdminEvents()
  const {
    participants,
    loading: pLoad,
    loadAll,
    create,
    update,
  } = useAdminParticipants(eventId)

  const [search, setSearch] = useState("")
  const [onlyMissing, setOnlyMissing] = useState(true)
  const [quickOpen, setQuickOpen] = useState(false)

  const event = useMemo(() => events.find((e) => e.id === eventId), [events, eventId])

  // Precarica
  useEffect(() => { loadAll() }, [loadAll, eventId])

  // Derived counters
  const counters = useMemo(() => {
    const total = participants.length
    const entered = participants.filter((p) => !!p.entered).length
    const missing = total - entered
    return { total, entered, missing }
  }, [participants])

  const normalized = useMemo(() => {
    const q = search.trim().toLowerCase()
    let list = participants
      .map((p) => ({
        ...p,
        _key: `${(p.name||"").toLowerCase()} ${(p.surname||"").toLowerCase()}`.trim(),
      }))
      .filter((p) => (q ? p._key.includes(q) : true))

    if (onlyMissing) list = list.filter((p) => p.entered !== true)

    // Order: missing first, then by surname/name
    return list.sort((a, b) => {
      if (!!a.entered !== !!b.entered) return a.entered ? 1 : -1
      const an = `${a.surname||""} ${a.name||""}`.toLowerCase()
      const bn = `${b.surname||""} ${b.name||""}`.toLowerCase()
      return an.localeCompare(bn)
    })
  }, [participants, search, onlyMissing])

  const markEntered = useCallback(async (p, value = true) => {
    try {
      await update(p.id, { entered: !!value, entered_at: new Date().toISOString() })
    } catch (e) {
      console.error(e)
    }
  }, [update])

  const quickAdd = useCallback(async ({ name, surname, email, birthdate }) => {
    try {
      await create({
        name, surname, email, birthdate,
        phone: "",
        price: event?.price ?? null,
        ticket_sent: false,
        location_sent: false,
        purchase_id: null,
        source: "door",
      })
      setQuickOpen(false)
    } catch (e) {
      console.error(e)
    }
  }, [create, event?.price])

  return (
    <div className="min-h-screen bg-black text-white p-4 lg:p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-4">
          {/* Top row: back + desktop actions */}
          <div className="flex items-center justify-between gap-2">
            <Button
              variant="ghost"
            onClick={() => router.push(routes.admin.eventDetails(eventId))}
              className="shrink-0 whitespace-nowrap"
            >
              <ArrowLeft className="h-4 w-4 mr-2"/> Torna all'evento
            </Button>
            {/* Desktop actions */}
            <div className="hidden sm:flex flex-wrap items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => loadAll()}
                className="shrink-0 whitespace-nowrap"
              >
                <RefreshCw className="h-4 w-4 mr-2"/> Aggiorna
              </Button>
              <Button
                size="sm"
                onClick={() => setQuickOpen(true)}
                className="shrink-0 whitespace-nowrap"
              >
                <UserPlus className="h-4 w-4 mr-2"/> Aggiungi
              </Button>
            </div>
          </div>
          {/* Mobile actions: full width under the back button */}
          <div className="mt-2 grid grid-cols-2 gap-2 sm:hidden">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadAll()}
              className="w-full justify-center whitespace-nowrap"
            >
              <RefreshCw className="h-4 w-4 mr-2"/> Aggiorna
            </Button>
            <Button
              size="sm"
              onClick={() => setQuickOpen(true)}
              className="w-full justify-center whitespace-nowrap"
            >
              <UserPlus className="h-4 w-4 mr-2"/> Aggiungi
            </Button>
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-end gap-4 mb-6">
          <div className="flex-1">
            <div className="text-2xl font-bold">{event?.title || "Evento"}</div>
            <div className="text-sm text-gray-400">{event?.date} • {event?.startTime} • {event?.location}</div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-zinc-900 rounded-md p-3 text-center">
              <div className="text-xs text-gray-400">Entrati</div>
              <div className="text-2xl font-bold text-emerald-400">{counters.entered}</div>
            </div>
            <div className="bg-zinc-900 rounded-md p-3 text-center">
              <div className="text-xs text-gray-400">Mancanti</div>
              <div className="text-2xl font-bold text-yellow-400">{counters.missing}</div>
            </div>
            <div className="bg-zinc-900 rounded-md p-3 text-center">
              <div className="text-xs text-gray-400">Totale</div>
              <div className="text-2xl font-bold text-blue-400">{counters.total}</div>
            </div>
          </div>
        </div>

        <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center mb-4">
          <Input
            placeholder="Cerca per nome e cognome…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-12 bg-zinc-900 border-zinc-700"
          />
          <div className="flex items-center gap-2 text-sm text-gray-300">
            <input
              id="only-missing-toggle"
              type="checkbox"
              checked={onlyMissing}
              onChange={(e) => {
                // debug + toggle
                // eslint-disable-next-line no-console
                console.debug("[Check-in] toggle onlyMissing ->", e.target.checked)
                setOnlyMissing(e.target.checked)
              }}
            />
            <Label htmlFor="only-missing-toggle" className="cursor-pointer">Mostra solo mancanti</Label>
          </div>
        </div>

        <div className="bg-zinc-900/60 rounded-lg border border-zinc-800">
          <div className="divide-y divide-zinc-800">
            {pLoad ? (
              <div className="flex justify-center items-center py-12">
                <Loader2 className="animate-spin h-6 w-6 mr-2"/> Caricamento…
              </div>
            ) : (
              normalized.length === 0 ? (
                <div className="text-center py-12 text-gray-400">Nessun risultato</div>
              ) : (
                normalized.map((p) => (
                  <div key={p.id} className="flex items-center justify-between p-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-2.5 h-2.5 rounded-full ${p.entered ? "bg-emerald-500" : "bg-yellow-500"}`}/>
                      <div>
                        <div className="font-medium">{p.name} {p.surname}</div>
                        <div className="text-xs text-gray-400">{p.email}</div>
                        {p.birthdate && <div className="text-xs text-gray-400">Data di nascita: {p.birthdate}</div>}
                      </div>
                      {p.membershipId ? (
                        <Badge variant="success">Membro</Badge>
                      ) : (
                        <Badge variant="secondary">No</Badge>
                      )}
                    </div>
                    <div>
                      {p.entered ? (
                        <Button variant="outline" onClick={() => markEntered(p, false)}>Annulla</Button>
                      ) : (
                        <Button onClick={() => markEntered(p, true)}>
                          <Check className="h-4 w-4 mr-1"/> Entra
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              )
            )}
          </div>
        </div>

        <QuickAddDialog open={quickOpen} onOpenChange={setQuickOpen} onSubmit={quickAdd} />
      </div>
    </div>
  )
}
