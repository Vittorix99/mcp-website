"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Loader2, ArrowLeft, Eye } from "lucide-react"
import { motion } from "framer-motion"
import { routes } from "@/config/routes"

import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardContent, CardTitle, CardFooter } from "@/components/ui/card"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { TooltipProvider } from "@/components/ui/tooltip"

import { useAdminPurchases } from "@/hooks/useAdminPurchases"
import { useAdminEvents } from "@/hooks/useAdminEvents"
import { PurchaseModal } from "@/components/admin/purchases/PurchaseModal"

export default function PurchasesPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const legacyPurchaseId = searchParams.get("purchaseId")
  const { purchases, loading } = useAdminPurchases()
  const { events } = useAdminEvents()

  const filtersKey = "mcp_admin_purchases_filters"
  const readFilters = () => {
    if (typeof window === "undefined") return {}
    try {
      return JSON.parse(window.localStorage.getItem(filtersKey) || "{}")
    } catch {
      return {}
    }
  }
  const stored = readFilters()

  const [search, setSearch] = useState(stored.search || "")
  const [dateFrom, setDateFrom] = useState(stored.dateFrom || "")
  const [dateTo, setDateTo] = useState(stored.dateTo || "")
  const [manualId, setManualId] = useState(stored.manualId || "")
  const [eventFilter, setEventFilter] = useState(stored.eventFilter || "all")
  const [dateSort, setDateSort] = useState(stored.dateSort || "desc")
  const [notFoundMsg, setNotFoundMsg] = useState("")
  const [selectedPurchase, setSelectedPurchase] = useState(null)

  useEffect(() => {
    if (legacyPurchaseId) {
      router.replace(routes.admin.purchasesDetails(legacyPurchaseId))
    }
  }, [legacyPurchaseId, router])

  useEffect(() => {
    if (typeof window === "undefined") return
    const payload = {
      search,
      dateFrom,
      dateTo,
      manualId,
      eventFilter,
      dateSort,
    }
    window.localStorage.setItem(filtersKey, JSON.stringify(payload))
  }, [search, dateFrom, dateTo, manualId, eventFilter, dateSort])

  const handleManualIdSearch = () => {
    if (!manualId) return
    const found = purchases.find(
      p => p.id === manualId ||
           p.transaction_id === manualId ||
           p.ref_id === manualId
    )
    if (found) {
      setSearch(found.payer_email)
      setDateFrom("")
      setDateTo("")
      setNotFoundMsg("")
    } else {
      setNotFoundMsg(`Nessun acquisto trovato per ID "${manualId}"`)
    }
  }

  const filtered = useMemo(() => {
    return purchases
      .filter(p => {
        const q = search.toLowerCase()
        if (search && !(
          p.payer_name.toLowerCase().includes(q) ||
          p.payer_surname.toLowerCase().includes(q) ||
          p.payer_email.toLowerCase().includes(q)
        )) return false

        if (eventFilter !== "all" && p.ref_id !== eventFilter) return false

        const ts = new Date(p.timestamp)
        if (dateFrom) {
          const from = new Date(dateFrom)
          from.setHours(0,0,0,0)
          if (ts < from) return false
        }
        if (dateTo) {
          const to = new Date(dateTo)
          to.setHours(23,59,59,999)
          if (ts > to) return false
        }
        return true
      })
      .sort((a, b) => {
        const diff = new Date(a.timestamp) - new Date(b.timestamp)
        return dateSort === "asc" ? diff : -diff
      })
  }, [purchases, search, dateFrom, dateTo, eventFilter, dateSort])

  const stats = useMemo(() => {
    const totalGross = filtered.reduce((sum, p) => sum + parseFloat(p.amount_total || "0"), 0)
    const totalFees = filtered.reduce((sum, p) => sum + parseFloat(p.paypal_fee || "0"), 0)
    const totalNet   = filtered.reduce((sum, p) => sum + parseFloat(p.net_amount || "0"), 0)
    return { totalGross, totalFees, totalNet }
  }, [filtered])

  const formatDate = iso =>
    new Date(iso).toLocaleDateString("it-IT", {
      day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit"
    })

  const resetFilters = () => {
    setSearch("")
    setDateFrom("")
    setDateTo("")
    setManualId("")
    setEventFilter("all")
    setDateSort("desc")
    setNotFoundMsg("")
    router.push(routes.admin.purchases)
  }

  const getPurchaseKey = (purchase) =>
    purchase.id || `${purchase.transaction_id || "purchase"}-${purchase.timestamp || "unknown"}`

  return (
    <TooltipProvider>
      <motion.div
        className="mx-auto space-y-6 p-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Button variant="ghost" onClick={() => router.push(routes.admin.dashboard)}>
          <ArrowLeft className="mr-2 h-4 w-4"/> Torna indietro
        </Button>
        <h1 className="text-3xl font-bold">Gestione Acquisti</h1>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card className="bg-zinc-900 border border-zinc-700">
            <CardHeader><CardTitle>Totale Lordo</CardTitle></CardHeader>
            <CardContent className="text-2xl font-bold">{stats.totalGross.toFixed(2)} €</CardContent>
          </Card>
          <Card className="bg-zinc-900 border border-zinc-700">
            <CardHeader><CardTitle>Totale Fee</CardTitle></CardHeader>
            <CardContent className="text-2xl font-bold">{stats.totalFees.toFixed(2)} €</CardContent>
          </Card>
          <Card className="bg-zinc-900 border border-zinc-700">
            <CardHeader><CardTitle>Totale Netto</CardTitle></CardHeader>
            <CardContent className="text-2xl font-bold">{stats.totalNet.toFixed(2)} €</CardContent>
          </Card>
        </div>

        <Card className="bg-zinc-900 border border-zinc-700">
          <CardContent className="p-4 space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <Input
                placeholder="Cerca nome, cognome o email..."
                className="flex-1"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
              <Select value={eventFilter} onValueChange={setEventFilter}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Filtra per evento" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti gli eventi</SelectItem>
                  {(events || []).map(ev => (
                    <SelectItem key={ev.id} value={ev.id}>
                      {ev.title}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                type="date"
                className="flex-1"
                value={dateFrom}
                onChange={e => setDateFrom(e.target.value)}
              />
              <Input
                type="date"
                className="flex-1"
                value={dateTo}
                onChange={e => setDateTo(e.target.value)}
              />
              <Select value={dateSort} onValueChange={setDateSort}>
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Ordina per data" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">Data: più recenti</SelectItem>
                  <SelectItem value="asc">Data: meno recenti</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col md:flex-row gap-4">
              <Input
                placeholder="Cerca per Transaction ID o Ref ID"
                className="flex-1"
                value={manualId}
                onChange={e => setManualId(e.target.value)}
              />
              <div className="flex gap-2">
                <Button onClick={handleManualIdSearch}>Cerca ID</Button>
                <Button variant="outline" onClick={resetFilters}>Reset</Button>
              </div>
            </div>
            {notFoundMsg && <p className="text-red-400">{notFoundMsg}</p>}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-0 md:p-6">
            {loading ? (
              <div className="py-12 flex justify-center">
                <Loader2 className="animate-spin h-8 w-8"/>
              </div>
            ) : (
              <>
                <div className="hidden md:block overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Pagante</TableHead>
                        <TableHead>Metodo</TableHead>
                        <TableHead>Importo</TableHead>
                        <TableHead>Data</TableHead>
                        <TableHead className="text-right">Dettagli</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filtered.map(p => (
                        <TableRow key={getPurchaseKey(p)}>
                          <TableCell>
                            <div className="font-medium">{p.payer_name} {p.payer_surname}</div>
                            <div className="text-sm text-gray-400">{p.payer_email}</div>
                          </TableCell>
                          <TableCell>{p.payment_method}</TableCell>
                          <TableCell>{parseFloat(p.amount_total).toFixed(2)} {p.currency}</TableCell>
                          <TableCell>{formatDate(p.timestamp)}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button size="icon" variant="ghost" onClick={() => setSelectedPurchase(p)}>
                                <Eye className="h-4 w-4"/>
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => router.push(routes.admin.purchasesDetails(p.id))}
                              >
                                Dettagli
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                <div className="md:hidden space-y-4 p-4">
                  {filtered.map(p => (
                    <Card key={getPurchaseKey(p)} className="bg-neutral-900 border-neutral-800">
                      <CardHeader className="flex justify-between items-center p-4">
                        <div>
                          <h3 className="font-bold">{p.payer_name} {p.payer_surname}</h3>
                          <p className="text-sm text-gray-400">{p.payer_email}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button size="icon" variant="ghost" onClick={() => setSelectedPurchase(p)}>
                            <Eye className="h-5 w-5"/>
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => router.push(routes.admin.purchasesDetails(p.id))}
                          >
                            Dettagli
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent className="p-4 pt-0 grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-semibold text-gray-400">Importo</p>
                          <p>{parseFloat(p.amount_total).toFixed(2)} {p.currency}</p>
                        </div>
                        <div>
                          <p className="font-semibold text-gray-400">Metodo</p>
                          <p className="truncate text-right">{p.payment_method}</p>
                        </div>
                      </CardContent>
                      <CardFooter className="p-4 pt-0">
                        <p className="text-xs text-gray-500 text-center">{formatDate(p.timestamp)}</p>
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              </>
            )}
            {!loading && filtered.length === 0 && (
              <div className="text-center py-12 text-gray-500">Nessun acquisto trovato.</div>
            )}
          </CardContent>
        </Card>

        {selectedPurchase && (
          <PurchaseModal
            purchase={selectedPurchase}
            onClose={() => {
              setSelectedPurchase(null)
            }}
          />
        )}
      </motion.div>
    </TooltipProvider>
  )
}
