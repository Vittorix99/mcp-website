"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Download, Loader2, Save, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { AdminLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { routes } from "@/config/routes"
import { getParticipantsByEvent } from "@/services/admin/participants"
import { getAllPurchases } from "@/services/admin/purchases"
import { disableDiscountCode, getDiscountCode, updateDiscountCode } from "@/services/admin/discountCodes"

function formatEuro(value) {
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR" }).format(Number(value || 0))
}

function formatDate(value) {
  if (!value) return "-"
  const date = value?.seconds ? new Date(value.seconds * 1000) : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" })
}

function escapeCsv(value) {
  const str = String(value ?? "")
  if (/[",\n]/.test(str)) return `"${str.replace(/"/g, '""')}"`
  return str
}

function downloadCsv(filename, rows) {
  const csv = rows.map((row) => row.map(escapeCsv).join(",")).join("\n")
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function discountLabel(code) {
  const type = code?.discountType || code?.discount_type
  const value = Number(code?.discountValue ?? code?.discount_value ?? 0)
  if (type === "PERCENTAGE") return `${value}%`
  if (type === "FIXED_PRICE") return `Prezzo finale ${formatEuro(value)}`
  return `Sconto ${formatEuro(value)}`
}

export default function DiscountCodeDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const discountCodeId = params?.id
  const [code, setCode] = useState(null)
  const [purchases, setPurchases] = useState([])
  const [participants, setParticipants] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [maxUses, setMaxUses] = useState("")
  const [isActive, setIsActive] = useState(false)

  const eventId = code?.eventId || code?.event_id

  const loadAll = async () => {
    if (!discountCodeId) return
    setLoading(true)
    const codeRes = await getDiscountCode(discountCodeId)
    if (codeRes?.error) {
      toast.error(codeRes.error)
      setLoading(false)
      return
    }
    setCode(codeRes)
    setMaxUses(String(codeRes.maxUses ?? codeRes.max_uses ?? ""))
    setIsActive(Boolean(codeRes.isActive ?? codeRes.is_active))

    const targetEventId = codeRes.eventId || codeRes.event_id
    const [purchaseRes, participantRes] = await Promise.all([
      getAllPurchases(),
      targetEventId ? getParticipantsByEvent(targetEventId) : Promise.resolve([]),
    ])
    setPurchases(Array.isArray(purchaseRes) ? purchaseRes : [])
    setParticipants(Array.isArray(participantRes) ? participantRes : [])
    setLoading(false)
  }

  useEffect(() => {
    loadAll()
  }, [discountCodeId])

  const filteredPurchases = useMemo(
    () => purchases.filter((purchase) => (purchase.discountCodeId || purchase.discount_code_id) === discountCodeId),
    [purchases, discountCodeId],
  )

  const filteredParticipants = useMemo(
    () => participants.filter((participant) => (participant.discountCodeId || participant.discount_code_id) === discountCodeId),
    [participants, discountCodeId],
  )

  const totals = useMemo(() => {
    const discountTotal = filteredPurchases.reduce((sum, purchase) => sum + Number(purchase.discountAmount ?? purchase.discount_amount ?? 0), 0)
    const netRevenue = filteredPurchases.reduce((sum, purchase) => sum + Number(purchase.amount_total || 0), 0)
    return { discountTotal, netRevenue }
  }, [filteredPurchases])

  const saveChanges = async () => {
    setSaving(true)
    const result = await updateDiscountCode(discountCodeId, {
      isActive,
      maxUses: Number.parseInt(maxUses, 10),
    })
    setSaving(false)
    if (result?.error) {
      toast.error(result.error)
      return
    }
    toast.success("Codice sconto aggiornato")
    setCode(result)
  }

  const deleteCode = async () => {
    const confirmed = window.confirm(`Disabilitare il codice sconto ${code.code}?`)
    if (!confirmed) return

    setSaving(true)
    const result = await disableDiscountCode(discountCodeId)
    setSaving(false)
    if (result?.error) {
      toast.error(result.error)
      return
    }
    toast.success("Codice sconto eliminato")
    setCode(result)
    setIsActive(false)
  }

  const exportPurchases = () => {
    downloadCsv(`acquisti_${code.code}.csv`, [
      ["Data", "Nome pagante", "Email", "Importo originale", "Sconto", "Importo pagato", "ID Acquisto"],
      ...filteredPurchases.map((purchase) => {
        const discount = Number(purchase.discountAmount ?? purchase.discount_amount ?? 0)
        const paid = Number(purchase.amount_total || 0)
        return [
          formatDate(purchase.timestamp),
          `${purchase.payer_name || ""} ${purchase.payer_surname || ""}`.trim(),
          purchase.payer_email || "",
          (paid + discount).toFixed(2),
          discount.toFixed(2),
          paid.toFixed(2),
          purchase.id,
        ]
      }),
    ])
  }

  const exportParticipants = () => {
    downloadCsv(`partecipanti_${code.code}.csv`, [
      ["Nome", "Cognome", "Email", "Prezzo originale", "Prezzo scontato", "Data acquisto"],
      ...filteredParticipants.map((participant) => [
        participant.name || "",
        participant.surname || "",
        participant.email || "",
        Number(participant.priceOriginal ?? participant.price_original ?? 0).toFixed(2),
        Number(participant.price || 0).toFixed(2),
        formatDate(participant.createdAt || participant.created_at),
      ]),
    ])
  }

  if (loading) return <AdminLoading label="Caricamento codice sconto..." />
  if (!code) {
    return (
      <div className="min-h-screen bg-black text-white p-6">
        <AdminPageHeader title="Codice sconto" backHref={routes.admin.events} backLabel="Torna agli eventi" />
        <p className="text-red-400">Codice sconto non trovato</p>
      </div>
    )
  }

  const usedCount = Number(code.usedCount ?? code.used_count ?? 0)
  const currentMaxUses = Number(code.maxUses ?? code.max_uses ?? 0)

  return (
    <div className="min-h-screen bg-black text-white p-6 space-y-6">
      <AdminPageHeader
        title={code.code}
        description={discountLabel(code)}
        backHref={eventId ? routes.admin.eventDiscountCodes(eventId) : routes.admin.events}
        backLabel="Torna ai codici"
        actions={(
          <>
            {eventId ? <Button variant="outline" onClick={() => router.push(routes.admin.eventDetails(eventId))}>Vai all'evento</Button> : null}
            <Button
              variant="destructive"
              onClick={deleteCode}
              disabled={saving || !isActive}
            >
              {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Trash2 className="mr-2 h-4 w-4" />}
              Elimina codice
            </Button>
          </>
        )}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card><CardContent className="p-4"><p className="text-sm text-gray-400">Utilizzi</p><p className="text-2xl font-bold">{usedCount} / {currentMaxUses}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-gray-400">Stato</p><div className="pt-1">{isActive ? <Badge className="bg-emerald-900/30 text-emerald-300 border-emerald-700">Attivo</Badge> : <Badge variant="secondary">Disabilitato</Badge>}</div></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-gray-400">Sconto erogato</p><p className="text-2xl font-bold">{formatEuro(totals.discountTotal)}</p></CardContent></Card>
        <Card><CardContent className="p-4"><p className="text-sm text-gray-400">Ricavo netto scontati</p><p className="text-2xl font-bold">{formatEuro(totals.netRevenue)}</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Modifica rapida</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-4 items-end">
          <div className="grid gap-2">
            <Label>Utilizzi massimi</Label>
            <Input type="number" min={usedCount || 1} value={maxUses} onChange={(event) => setMaxUses(event.target.value)} />
          </div>
          <label className="flex items-center gap-2 pb-2">
            <Switch checked={isActive} onCheckedChange={setIsActive} />
            <span className="text-sm text-gray-300">Attivo</span>
          </label>
          <Button onClick={saveChanges} disabled={saving}>
            {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
            Salva
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Acquisti con questo codice</CardTitle>
          <Button variant="outline" onClick={exportPurchases} disabled={!filteredPurchases.length}><Download className="mr-2 h-4 w-4" />Esporta CSV</Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Nome pagante</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Importo originale</TableHead>
                  <TableHead>Sconto</TableHead>
                  <TableHead>Importo pagato</TableHead>
                  <TableHead>ID Acquisto</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredPurchases.map((purchase) => {
                  const discount = Number(purchase.discountAmount ?? purchase.discount_amount ?? 0)
                  const paid = Number(purchase.amount_total || 0)
                  return (
                    <TableRow key={purchase.id} className="cursor-pointer" onClick={() => router.push(routes.admin.purchasesDetails(purchase.id))}>
                      <TableCell>{formatDate(purchase.timestamp)}</TableCell>
                      <TableCell>{purchase.payer_name} {purchase.payer_surname}</TableCell>
                      <TableCell>{purchase.payer_email}</TableCell>
                      <TableCell>{formatEuro(paid + discount)}</TableCell>
                      <TableCell>{formatEuro(discount)}</TableCell>
                      <TableCell>{formatEuro(paid)}</TableCell>
                      <TableCell className="font-mono text-xs">{purchase.id}</TableCell>
                    </TableRow>
                  )
                })}
                {!filteredPurchases.length && <TableRow><TableCell colSpan={7} className="text-center py-10 text-gray-400">Nessun acquisto trovato.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Partecipanti che hanno usato questo codice</CardTitle>
          <Button variant="outline" onClick={exportParticipants} disabled={!filteredParticipants.length}><Download className="mr-2 h-4 w-4" />Esporta CSV</Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nome</TableHead>
                  <TableHead>Cognome</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Prezzo originale</TableHead>
                  <TableHead>Prezzo scontato</TableHead>
                  <TableHead>Data acquisto</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredParticipants.map((participant) => (
                  <TableRow key={participant.id}>
                    <TableCell>{participant.name}</TableCell>
                    <TableCell>{participant.surname}</TableCell>
                    <TableCell>{participant.email}</TableCell>
                    <TableCell>{formatEuro(participant.priceOriginal ?? participant.price_original)}</TableCell>
                    <TableCell>{formatEuro(participant.price)}</TableCell>
                    <TableCell>{formatDate(participant.createdAt || participant.created_at)}</TableCell>
                  </TableRow>
                ))}
                {!filteredParticipants.length && <TableRow><TableCell colSpan={6} className="text-center py-10 text-gray-400">Nessun partecipante trovato.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
