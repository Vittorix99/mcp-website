"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Loader2, Plus, RefreshCw, Tag, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { AdminLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { routes } from "@/config/routes"
import { getEventById } from "@/services/admin/events"
import { createDiscountCode, disableDiscountCode, listDiscountCodes, updateDiscountCode } from "@/services/admin/discountCodes"

const DISCOUNT_TYPES = [
  { value: "PERCENTAGE", label: "Percentuale" },
  { value: "FIXED", label: "Importo fisso" },
  { value: "FIXED_PRICE", label: "Prezzo finale" },
]

const emptyForm = {
  code: "",
  discountType: "PERCENTAGE",
  discountValue: "",
  maxUses: "1",
  restriction: "none",
  restrictedMembershipId: "",
  restrictedEmail: "",
}

function formatDiscount(code) {
  const value = Number(code.discountValue ?? code.discount_value ?? 0)
  const type = code.discountType || code.discount_type
  if (type === "PERCENTAGE") return `${value}%`
  if (type === "FIXED_PRICE") return `Prezzo ${formatEuro(value)}`
  return `-${formatEuro(value)}`
}

function formatEuro(value) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(Number(value || 0))
}

function statusBadge(code) {
  const used = Number(code.usedCount ?? code.used_count ?? 0)
  const max = Number(code.maxUses ?? code.max_uses ?? 0)
  const active = Boolean(code.isActive ?? code.is_active)
  if (used >= max) return <Badge className="bg-red-900/30 text-red-300 border-red-700">Esaurito</Badge>
  if (!active) return <Badge variant="secondary">Disabilitato</Badge>
  return <Badge className="bg-emerald-900/30 text-emerald-300 border-emerald-700">Attivo</Badge>
}

function CreateDiscountDialog({ open, onOpenChange, onSubmit, saving }) {
  const [form, setForm] = useState(emptyForm)

  useEffect(() => {
    if (!open) setForm(emptyForm)
  }, [open])

  const setField = (key, value) => {
    setForm((current) => ({ ...current, [key]: key === "code" ? value.toUpperCase() : value }))
  }

  const submit = (event) => {
    event.preventDefault()
    const payload = {
      code: form.code.trim().toUpperCase(),
      discountType: form.discountType,
      discountValue: Number(form.discountValue),
      maxUses: Number.parseInt(form.maxUses, 10),
    }
    if (form.restriction === "membership") payload.restrictedMembershipId = form.restrictedMembershipId.trim()
    if (form.restriction === "email") payload.restrictedEmail = form.restrictedEmail.trim().toLowerCase()
    onSubmit(payload)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nuovo codice sconto</DialogTitle>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-2">
            <Label>Codice</Label>
            <Input value={form.code} onChange={(event) => setField("code", event.target.value)} required />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="grid gap-2">
              <Label>Tipo sconto</Label>
              <select className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={form.discountType} onChange={(event) => setField("discountType", event.target.value)}>
                {DISCOUNT_TYPES.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            </div>
            <div className="grid gap-2">
              <Label>Valore</Label>
              <Input type="number" min="0.01" step="0.01" value={form.discountValue} onChange={(event) => setField("discountValue", event.target.value)} required />
            </div>
          </div>
          <div className="grid gap-2">
            <Label>Utilizzi massimi</Label>
            <Input type="number" min="1" step="1" value={form.maxUses} onChange={(event) => setField("maxUses", event.target.value)} required />
          </div>
          <div className="grid gap-2">
            <Label>Restrizione</Label>
            <select className="h-10 rounded-md border border-input bg-background px-3 text-sm" value={form.restriction} onChange={(event) => setField("restriction", event.target.value)}>
              <option value="none">Nessuna</option>
              <option value="membership">Per Membership ID</option>
              <option value="email">Per Email</option>
            </select>
          </div>
          {form.restriction === "membership" && (
            <div className="grid gap-2">
              <Label>Membership ID</Label>
              <Input value={form.restrictedMembershipId} onChange={(event) => setField("restrictedMembershipId", event.target.value)} required />
            </div>
          )}
          {form.restriction === "email" && (
            <div className="grid gap-2">
              <Label>Email</Label>
              <Input type="email" value={form.restrictedEmail} onChange={(event) => setField("restrictedEmail", event.target.value)} required />
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
            <Button type="submit" disabled={saving}>
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Crea
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function EventDiscountCodesPage() {
  const params = useParams()
  const router = useRouter()
  const eventId = params?.id
  const [event, setEvent] = useState(null)
  const [codes, setCodes] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [dialogOpen, setDialogOpen] = useState(false)

  const loadAll = async () => {
    if (!eventId) return
    setLoading(true)
    const [eventRes, codesRes] = await Promise.all([
      getEventById(eventId),
      listDiscountCodes(eventId),
    ])
    if (!eventRes?.error) setEvent(eventRes?.event || eventRes)
    if (codesRes?.error) {
      toast.error(codesRes.error)
      setCodes([])
    } else {
      setCodes(Array.isArray(codesRes) ? codesRes : [])
    }
    setLoading(false)
  }

  useEffect(() => {
    loadAll()
  }, [eventId])

  const counters = useMemo(() => {
    const active = codes.filter((code) => Boolean(code.isActive ?? code.is_active)).length
    const used = codes.reduce((sum, code) => sum + Number(code.usedCount ?? code.used_count ?? 0), 0)
    return { active, used }
  }, [codes])

  const handleCreate = async (payload) => {
    setSaving(true)
    const result = await createDiscountCode(eventId, payload)
    setSaving(false)
    if (result?.error) {
      toast.error(result.error)
      return
    }
    toast.success("Codice sconto creato")
    setDialogOpen(false)
    loadAll()
  }

  const handleToggle = async (code, value) => {
    const id = code.id
    const result = await updateDiscountCode(id, { isActive: value })
    if (result?.error) {
      toast.error(result.error)
      return
    }
    setCodes((items) => items.map((item) => item.id === id ? { ...item, isActive: value, is_active: value } : item))
  }

  const handleDelete = async (code) => {
    const confirmed = window.confirm(`Disabilitare il codice sconto ${code.code}?`)
    if (!confirmed) return

    const result = await disableDiscountCode(code.id)
    if (result?.error) {
      toast.error(result.error)
      return
    }
    toast.success("Codice sconto eliminato")
    setCodes((items) => items.map((item) => item.id === code.id ? { ...item, isActive: false, is_active: false } : item))
  }

  if (loading) return <AdminLoading label="Caricamento codici sconto..." />

  return (
    <div className="min-h-screen bg-black text-white p-6 space-y-6">
      <AdminPageHeader
        title="Codici sconto"
        description={event?.title || eventId}
        backHref={routes.admin.eventDetails(eventId)}
        backLabel="Torna all'evento"
        actions={(
          <>
            <Button variant="outline" onClick={loadAll}><RefreshCw className="mr-2 h-4 w-4" />Aggiorna</Button>
            <Button onClick={() => setDialogOpen(true)}><Plus className="mr-2 h-4 w-4" />Nuovo codice sconto</Button>
          </>
        )}
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card><CardContent className="p-4"><p className="text-sm text-gray-400">Codici totali</p><p className="text-2xl font-bold">{codes.length}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-gray-400">Codici attivi</p><p className="text-2xl font-bold">{counters.active}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-gray-400">Utilizzi totali</p><p className="text-2xl font-bold">{counters.used}</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><Tag className="h-5 w-5 text-mcp-orange" />Codici</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Codice</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Valore</TableHead>
                  <TableHead>Usati / Max</TableHead>
                  <TableHead>Riservato a</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead>Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {codes.map((code) => {
                  const restricted = code.restrictedMembershipId || code.restricted_membership_id || code.restrictedEmail || code.restricted_email || "Nessuno"
                  const used = Number(code.usedCount ?? code.used_count ?? 0)
                  const max = Number(code.maxUses ?? code.max_uses ?? 0)
                  const active = Boolean(code.isActive ?? code.is_active)
                  return (
                    <TableRow key={code.id} className="cursor-pointer" onClick={() => router.push(routes.admin.discountCodeDetails(code.id))}>
                      <TableCell className="font-mono font-semibold">{code.code}</TableCell>
                      <TableCell>{DISCOUNT_TYPES.find((item) => item.value === (code.discountType || code.discount_type))?.label || code.discountType || code.discount_type}</TableCell>
                      <TableCell>{formatDiscount(code)}</TableCell>
                      <TableCell>{used} / {max}</TableCell>
                      <TableCell>{restricted}</TableCell>
                      <TableCell>{statusBadge(code)}</TableCell>
                      <TableCell onClick={(event) => event.stopPropagation()}>
                        <div className="flex items-center gap-2">
                          <Switch checked={active} onCheckedChange={(value) => handleToggle(code, value)} />
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-red-300 hover:text-red-200 hover:bg-red-950/30"
                            onClick={() => handleDelete(code)}
                            aria-label={`Elimina codice ${code.code}`}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
                {!codes.length && (
                  <TableRow><TableCell colSpan={7} className="text-center py-10 text-gray-400">Nessun codice sconto per questo evento.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <CreateDiscountDialog open={dialogOpen} onOpenChange={setDialogOpen} onSubmit={handleCreate} saving={saving} />
    </div>
  )
}
