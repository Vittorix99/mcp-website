"use client"

import { useEffect, useMemo, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { routes } from "@/config/routes"
import { EVENT_STATUSES } from "@/config/events-utils"
import { getPurchaseById } from "@/services/admin/purchases"
import { getParticipantsByEvent } from "@/services/admin/participants"
import { getEventById } from "@/services/admin/events"
import { AdminLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"

export default function PurchaseDetailsPage() {
  const router = useRouter()
  const params = useParams()
  const purchaseId = params?.id

  const [purchase, setPurchase] = useState(null)
  const [event, setEvent] = useState(null)
  const [participants, setParticipants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let isMounted = true

    async function loadPurchase() {
      if (!purchaseId) return
      setLoading(true)
      setError("")

      const res = await getPurchaseById(purchaseId)
      if (!isMounted) return

      if (res?.error) {
        setError(res.error)
        setPurchase(null)
        setLoading(false)
        return
      }

      setPurchase(res)

      if (res?.ref_id) {
        const [eventRes, participantsRes] = await Promise.all([
          getEventById(res.ref_id),
          getParticipantsByEvent(res.ref_id),
        ])

        if (!isMounted) return

        if (!eventRes?.error) {
          setEvent(eventRes?.event || eventRes)
        }

        if (!participantsRes?.error && Array.isArray(participantsRes)) {
          const filtered = participantsRes.filter((p) => p.purchase_id === res.id)
          setParticipants(filtered)
        } else {
          setParticipants([])
        }
      }

      setLoading(false)
    }

    loadPurchase()

    return () => {
      isMounted = false
    }
  }, [purchaseId])

  const participantsCount = purchase?.participants_count ?? participants.length

  if (loading) {
    return <AdminLoading label="Caricamento acquisto..." />
  }

  if (error || !purchase) {
    return (
      <div className="min-h-screen bg-black text-white p-6">
        <AdminPageHeader title="Dettagli acquisto" backHref={routes.admin.purchases} backLabel="Torna agli acquisti" />
        <p className="mt-6 text-red-400">{error || "Acquisto non trovato"}</p>
      </div>
    )
  }

  const formatDate = (iso) =>
    new Date(iso).toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })

  const parseEventDate = (dateStr, timeStr) => {
    if (!dateStr) return null
    let dateObj = null
    if (dateStr.includes("-")) {
      const parts = dateStr.split("-")
      if (parts.length === 3 && parts[0].length === 2) {
        const [day, month, year] = parts.map(Number)
        dateObj = new Date(year, month - 1, day)
      }
    }
    if (!dateObj || Number.isNaN(dateObj.getTime())) {
      const parsed = new Date(dateStr)
      if (!Number.isNaN(parsed.getTime())) {
        dateObj = parsed
      }
    }
    if (!dateObj) return null
    if (timeStr) {
      const [h, m] = String(timeStr).split(":").map(Number)
      if (!Number.isNaN(h)) dateObj.setHours(h)
      if (!Number.isNaN(m)) dateObj.setMinutes(m)
    }
    return dateObj
  }

  const getDisplayStatus = (ev) => {
    if (!ev) return EVENT_STATUSES.ACTIVE
    const rawStatus = ev.status
    if (rawStatus && rawStatus !== EVENT_STATUSES.ACTIVE) return rawStatus
    const eventDate = parseEventDate(ev.date, ev.startTime)
    if (eventDate && eventDate.getTime() < Date.now()) {
      return EVENT_STATUSES.ENDED
    }
    return rawStatus || EVENT_STATUSES.ACTIVE
  }

  return (
    <div className="min-h-screen bg-black text-white p-6 space-y-6">
      <AdminPageHeader
        title="Dettagli acquisto"
        description={purchase.id}
        backHref={routes.admin.purchases}
        backLabel="Torna agli acquisti"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="bg-zinc-900 border-zinc-700">
          <CardHeader>
            <CardTitle>Totale</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold">
            {parseFloat(purchase.amount_total || "0").toFixed(2)} {purchase.currency || "EUR"}
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-700">
          <CardHeader>
            <CardTitle>Partecipanti</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold">{participantsCount}</CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-700">
          <CardHeader>
            <CardTitle>Membership collegate</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold">
            {participants.filter((p) => p.membershipId || p.membership_id).length}
          </CardContent>
        </Card>
      </div>

      <Card className="bg-zinc-900 border-zinc-700">
        <CardHeader>
          <CardTitle>Riepilogo pagamento</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between border-b border-zinc-800 pb-2">
            <span className="text-gray-400">Pagante</span>
            <span>{purchase.payer_name} {purchase.payer_surname}</span>
          </div>
          <div className="flex justify-between border-b border-zinc-800 pb-2">
            <span className="text-gray-400">Email</span>
            <span>{purchase.payer_email || "-"}</span>
          </div>
          <div className="flex justify-between border-b border-zinc-800 pb-2">
            <span className="text-gray-400">Metodo</span>
            <span>{purchase.payment_method || "-"}</span>
          </div>
          <div className="flex justify-between border-b border-zinc-800 pb-2">
            <span className="text-gray-400">Status</span>
            <span>{purchase.status || "-"}</span>
          </div>
          <div className="flex justify-between border-b border-zinc-800 pb-2">
            <span className="text-gray-400">Transaction ID</span>
            <span>{purchase.transaction_id || "-"}</span>
          </div>
          <div className="flex justify-between border-b border-zinc-800 pb-2">
            <span className="text-gray-400">Order ID</span>
            <span>{purchase.order_id || "-"}</span>
          </div>
          <div className="flex justify-between border-b border-zinc-800 pb-2">
            <span className="text-gray-400">Ref ID</span>
            <span>{purchase.ref_id || "-"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Timestamp</span>
            <span>{purchase.timestamp ? formatDate(purchase.timestamp) : "-"}</span>
          </div>
        </CardContent>
      </Card>

      {event && (
        <Card className="bg-zinc-900 border-zinc-700">
          <CardHeader>
            <CardTitle>Evento</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <p className="text-lg font-semibold">{event.title}</p>
              <p className="text-sm text-gray-400">{event.date} • {event.startTime}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={getDisplayStatus(event) === EVENT_STATUSES.ACTIVE ? "success" : "secondary"}>
                {getDisplayStatus(event)}
              </Badge>
              <Button size="sm" onClick={() => router.push(routes.admin.eventDetails(event.id))}>
                Vai all'evento
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="bg-zinc-900 border-zinc-700">
        <CardHeader>
          <CardTitle>Partecipanti ({participants.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {participants.length ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Telefono</TableHead>
                    <TableHead>Membro</TableHead>
                    <TableHead>Ticket</TableHead>
                    <TableHead>Location</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {participants.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{p.name} {p.surname}</TableCell>
                      <TableCell>{p.email}</TableCell>
                      <TableCell>{p.phone || "-"}</TableCell>
                      <TableCell>
                        {p.membershipId || p.membership_id ? (
                          <Button
                            size="sm"
                            onClick={() =>
                              router.push(
                                routes.admin.membershipDetails(p.membershipId || p.membership_id)
                              )
                            }
                          >
                            Vai al membro
                          </Button>
                        ) : (
                          "-"
                        )}
                      </TableCell>
                      <TableCell>{p.ticket_sent ? "Sì" : "No"}</TableCell>
                      <TableCell>{p.location_sent ? "Sì" : "No"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <p className="text-sm text-gray-400">Nessun partecipante trovato per questo acquisto.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
