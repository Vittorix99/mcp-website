"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, Loader2, Download, Eye, Ticket, Trash2, Edit, MoreVertical, Wallet, SlidersHorizontal, AlertTriangle } from "lucide-react"
import { motion } from "framer-motion"
import * as XLSX from "xlsx"
import {routes} from "@/config/routes"

import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

import MembershipStats from "@/components/admin/memberships/MembershipStats"
import { useAdminMemberships } from "@/hooks/useAdminMemberships"
import { useAdminEvents } from "@/hooks/useAdminEvents"
import { MembershipModal } from "@/components/admin/memberships/MembershipsModal"
import { useError } from "@/contexts/errorContext"
import { getMembershipsReport } from "@/services/admin/memberships"

export default function MembershipsPage() {
  const router = useRouter()
  const yearStorageKey = "mcp_admin_memberships_year"
  const {
    memberships,
    loadAll,
    create,
    update,
    remove,
    sendCard,
    getMembershipPriceForYear,
    setMembershipPriceForYear,
    membershipPrice,
    isMembershipPriceReadOnly,
    walletModelId,
    fetchWalletModel,
    saveWalletModel,
    loading,
  } = useAdminMemberships()
  const { events } = useAdminEvents()
  const { setError } = useError()

  const filtersKey = "mcp_admin_memberships_filters"
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
  const [showOnlyNotSent, setShowOnlyNotSent] = useState(!!stored.showOnlyNotSent)
  const [modalOpen, setModalOpen] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [form, setForm] = useState({})
  const [initial, setInitial] = useState({})
  const [priceEditing, setPriceEditing] = useState(false)
  const [tempPrice, setTempPrice] = useState("")
  const [walletModelEditing, setWalletModelEditing] = useState(false)
  const [tempWalletModel, setTempWalletModel] = useState("")
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [settingsTab, setSettingsTab] = useState("price")
  const [walletModelWarningOpen, setWalletModelWarningOpen] = useState(false)
  const [walletModelWarningText, setWalletModelWarningText] = useState(
    "Modello Wallet Pass2U non configurato. Configuralo dalle impostazioni."
  )
  const [selectedYear, setSelectedYear] = useState(() => {
    if (typeof window === "undefined") {
      return new Date().getFullYear().toString()
    }
    const stored = window.localStorage.getItem(yearStorageKey)
    if (stored) return stored
    const match = document.cookie.match(/(?:^|; )mcp_admin_memberships_year=([^;]*)/)
    return match ? decodeURIComponent(match[1]) : new Date().getFullYear().toString()
  })
  const [selectedEventId, setSelectedEventId] = useState(stored.selectedEventId || "")
  const [exportEventLoading, setExportEventLoading] = useState(false)
  const [sortBy, setSortBy] = useState(stored.sortBy || "name_asc")
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(stored.pageSize || 25)

  const currentYear = new Date().getFullYear().toString()

  useEffect(() => {
    getMembershipPriceForYear(selectedYear)
  }, [getMembershipPriceForYear, selectedYear])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const result = await fetchWalletModel()
      if (cancelled || !result) return
      if (result.missing) {
        if (result.message) setWalletModelWarningText(result.message)
        setWalletModelWarningOpen(true)
      }
    })()

    return () => {
      cancelled = true
    }
  }, [fetchWalletModel])

  useEffect(() => {
    if (typeof window === "undefined") return
    window.localStorage.setItem(yearStorageKey, selectedYear)
    document.cookie = `${yearStorageKey}=${encodeURIComponent(selectedYear)}; path=/; max-age=31536000`
  }, [selectedYear])

  useEffect(() => {
    if (typeof window === "undefined") return
    const payload = {
      search,
      showOnlyNotSent,
      sortBy,
      selectedEventId,
      pageSize,
    }
    window.localStorage.setItem(filtersKey, JSON.stringify(payload))
  }, [search, showOnlyNotSent, sortBy, selectedEventId, pageSize])

  const exportExcel = () => {
    const filteredData = filtered.map((m) => ({
      Nome: m.name,
      Cognome: m.surname,
      Email: m.email,
      "Inviata tessera": m.membership_sent ? "Sì" : "No",
      "Valida fino a": m.end_date,
    }))
    const ws = XLSX.utils.json_to_sheet(filteredData)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, "Membri")
    XLSX.writeFile(wb, `membri_${Date.now()}.xlsx`)
  }

  const exportEventExcel = async () => {
    if (!selectedEventId) {
      setError("Seleziona un evento per esportare.")
      return
    }
    setExportEventLoading(true)
    try {
      const res = await getMembershipsReport(selectedEventId)
      if (res?.error) {
        setError(res.error)
        return
      }
      const rows = res?.rows || []
      const reportData = rows.map((r) => ({
        "Data iscrizione": r.data_iscrizione || "",
        Nome: r.name || "",
        Cognome: r.surname || "",
        Email: r.email || "",
        Associato: r.associato || "",
        "Netto pagato": r.netto_pagato ?? "",
        "Quota variabile": r.quota_variabile ?? "",
      }))

      const summaryData = [
        {
          Evento: eventOptionsMap[selectedEventId] || selectedEventId,
          "Nuovi associati": res?.new_associates_count ?? 0,
          "Associati gia registrati": res?.existing_associates_count ?? 0,
          "Totale netto incassato": res?.total_net_collected ?? 0,
        },
      ]

      const wb = XLSX.utils.book_new()
      const wsSummary = XLSX.utils.json_to_sheet(summaryData)
      XLSX.utils.book_append_sheet(wb, wsSummary, "Riepilogo")
      const wsReport = XLSX.utils.json_to_sheet(reportData)
      XLSX.utils.book_append_sheet(wb, wsReport, "Associati")

      const rawTitle = eventOptionsMap[selectedEventId] || selectedEventId
      const safeTitle = rawTitle
        .toString()
        .replace(/\s+/g, "_")
        .replace(/[^a-zA-Z0-9_-]/g, "")
      const filename = `associati_evento_${safeTitle}.xlsx`
      XLSX.writeFile(wb, filename)
    } catch (e) {
      console.error("exportEventExcel error", e)
      setError("Errore esportazione report evento.")
    } finally {
      setExportEventLoading(false)
    }
  }

  const parseEventDate = (value) => {
    if (!value) return null
    if (value.includes("-")) {
      const parts = value.split("-")
      if (parts.length === 3 && parts[0].length === 2) {
        const [day, month, year] = parts.map(Number)
        return new Date(year, month - 1, day)
      }
    }
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  const getClosestEvent = (isoDate) => {
    if (!isoDate || !eventOptions.length) return null
    const target = new Date(isoDate)
    if (Number.isNaN(target.getTime())) return null

    let closest = null
    let bestDiff = Number.POSITIVE_INFINITY
    eventOptions.forEach((ev) => {
      const evDate = parseEventDate(ev.date)
      if (!evDate) return
      const diff = Math.abs(target - evDate)
      if (diff < bestDiff) {
        bestDiff = diff
        closest = ev
      }
    })
    return closest
  }

  const exportManualMembers = () => {
    const manualMembers = memberships.filter((m) => !m.purchase_id)
    if (!manualMembers.length) {
      setError("Nessun membro onorario da esportare.")
      return
    }

    const rows = manualMembers.map((m) => {
      const closestEvent = getClosestEvent(m.start_date)
      const eventLabel = closestEvent
        ? (closestEvent.date ? `${closestEvent.title} (${closestEvent.date})` : closestEvent.title)
        : ""
      return {
        "Data iscrizione": m.start_date || "",
        Nome: m.name || "",
        Cognome: m.surname || "",
        Email: m.email || "",
        "Evento piu vicino": eventLabel || "",
      }
    })

    const ws = XLSX.utils.json_to_sheet(rows)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, "Membri onorari")
    XLSX.writeFile(wb, "membri_onorari.xlsx")
  }

  const parseMembershipDate = (value) => {
    if (!value) return null
    const raw = String(value).trim()
    if (!raw) return null

    if (/^\d{2}-\d{2}-\d{4}$/.test(raw)) {
      const [day, month, year] = raw.split("-").map(Number)
      const parsed = new Date(year, month - 1, day)
      return Number.isNaN(parsed.getTime()) ? null : parsed
    }

    const parsed = new Date(raw)
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  const getMembershipYear = (m) => {
    const startDate = parseMembershipDate(m?.start_date)
    if (startDate) {
      return startDate.getFullYear().toString()
    }

    const endDate = parseMembershipDate(m?.end_date)
    if (endDate) {
      const isFirstDayOfYear =
        endDate.getDate() === 1 && endDate.getMonth() === 0
      const year = isFirstDayOfYear
        ? endDate.getFullYear() - 1
        : endDate.getFullYear()
      return year.toString()
    }

    return null
  }

  const yearOptions = useMemo(() => {
    const years = new Set()
    memberships.forEach((m) => {
      const y = getMembershipYear(m)
      if (y) years.add(y)
    })
    years.add(currentYear)
    if (selectedYear) years.add(selectedYear)
    return Array.from(years).sort((a, b) => b.localeCompare(a))
  }, [memberships, currentYear, selectedYear])

  useEffect(() => {
    if (!yearOptions.includes(selectedYear)) {
      setSelectedYear(currentYear)
    }
  }, [yearOptions, selectedYear, currentYear])

  const eventOptions = useMemo(() => {
    return (events || []).slice().sort((a, b) => {
      const aDate = new Date(a.date || 0).getTime()
      const bDate = new Date(b.date || 0).getTime()
      return bDate - aDate
    })
  }, [events])

  const eventOptionsMap = useMemo(() => {
    const map = {}
    eventOptions.forEach((ev) => {
      const label = ev.date ? `${ev.title} (${ev.date})` : ev.title
      map[ev.id] = label || ev.id
    })
    return map
  }, [eventOptions])

  const filtered = useMemo(() => {
    const s = (search || "").toLowerCase()

    return memberships.filter((m) => {
      const fullName = `${m.name || ""} ${m.surname || ""}`.toLowerCase()
      const phoneVal = (m.phone || "")
      const emailVal = (m.email || "").toLowerCase()

      const y = getMembershipYear(m)
      if (selectedYear && y !== selectedYear) return false
      if (
        s &&
        !(
          fullName.includes(s) ||
          emailVal.includes(s) ||
          phoneVal.includes(s)
        )
      ) {
        return false
      }
      if (showOnlyNotSent && !!m.membership_sent) return false
      return true
    })
  }, [memberships, search, showOnlyNotSent, selectedYear])

  const sortedMembers = useMemo(() => {
    const list = [...filtered]
    const nameKey = (m) => `${m.name || ""} ${m.surname || ""}`.trim().toLowerCase()
    const eventsCount = (m) => (m.attended_events || []).length
    const dateKey = (m) => {
      const raw = m.start_date || m.end_date || ""
      const ts = raw ? new Date(raw).getTime() : Number.NEGATIVE_INFINITY
      return Number.isNaN(ts) ? Number.NEGATIVE_INFINITY : ts
    }

    switch (sortBy) {
      case "name_desc":
        return list.sort((a, b) => nameKey(b).localeCompare(nameKey(a)))
      case "events_asc":
        return list.sort((a, b) => eventsCount(a) - eventsCount(b))
      case "events_desc":
        return list.sort((a, b) => eventsCount(b) - eventsCount(a))
      case "date_desc":
        return list.sort((a, b) => dateKey(b) - dateKey(a))
      case "date_asc":
        return list.sort((a, b) => dateKey(a) - dateKey(b))
      case "name_asc":
      default:
        return list.sort((a, b) => nameKey(a).localeCompare(nameKey(b)))
    }
  }, [filtered, sortBy])

  useEffect(() => {
    setPage(1)
  }, [search, showOnlyNotSent, selectedYear, sortBy, selectedEventId, memberships.length])

  const totalItems = sortedMembers.length
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
  const clampedPage = Math.min(page, totalPages)
  const startIndex = (clampedPage - 1) * pageSize
  const endIndex = Math.min(startIndex + pageSize, totalItems)
  const paginatedMembers = sortedMembers.slice(startIndex, endIndex)

  const stats = useMemo(
    () => ({
      total: filtered.length,
      valid: filtered.filter((m) => m.subscription_valid).length,
      manual: filtered.filter((m) => !m.purchase_id).length,
    }),
    [filtered],
  )

  const totalTesseramenti = useMemo(() => {
    if (!membershipPrice || membershipPrice.year !== selectedYear) return 0
    const count = memberships.filter((m) => {
      const d = new Date(m.start_date)
      return !Number.isNaN(d.getTime()) && d.getFullYear().toString() === selectedYear
    }).length
    return count * membershipPrice.price
  }, [memberships, membershipPrice, selectedYear])

  const onSavePrice = async () => {
    if (isMembershipPriceReadOnly) return
    const val = Number.parseFloat(tempPrice)
    if (!isNaN(val)) {
      await setMembershipPriceForYear(selectedYear, val)
      setPriceEditing(false)
    }
  }

  const openSettings = (tab = "price") => {
    setSettingsTab(tab)
    setPriceEditing(false)
    setWalletModelEditing(false)
    // Defer to let DropdownMenu fully unmount before Dialog opens,
    // otherwise Radix leaves pointer-events:none on <body> and the UI freezes.
    setTimeout(() => setSettingsOpen(true), 0)
  }

  const openForm = (m = null) => {
    if (m) {
      setEditMode(true)
      setForm({ ...m })
      setInitial({ ...m })
    } else {
      setEditMode(false)
      setForm({ name: "", surname: "", email: "", phone: "", birthdate: "", send_card_on_create: false })
      setInitial({})
    }
    setModalOpen(true)
  }

  const closeForm = () => {
    setModalOpen(false)
    setForm({})
    setInitial({})
    setEditMode(false)
  }

  const submitForm = async (e) => {
    e.preventDefault()
    if (editMode) {
      const diff = {}
      Object.keys(form).forEach((k) => {
        if (form[k] !== initial[k]) diff[k] = form[k]
      })
      if (Object.keys(diff).length) await update(form.id, diff)
    } else await create(form)
    closeForm()
  }

  function isExpired(endDateStr) {
    if (!endDateStr) return true
    const [d, m, y] = endDateStr.split("-").map(Number)
    return new Date(y, m - 1, d, 23, 59, 59) < new Date()
  }

  const formatDate = (iso) => {
    if (!iso) return "-"
    return new Date(iso).toLocaleDateString("it-IT", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    })
  }

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-6 pb-8"
      >
        <div>
                <Button variant="ghost" onClick={() => router.push(routes.admin.dashboard)}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Torna admin
          </Button>
          
          <h1 className="text-3xl md:text-4xl font-bold gradient-text mt-2">Gestione Membri</h1>
          <p className="text-gray-300">Crea, modifica e gestisci eventi MCP.</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedYear} onValueChange={setSelectedYear}>
            <SelectTrigger className="min-w-[160px]">
              <SelectValue placeholder="Anno" />
            </SelectTrigger>
            <SelectContent>
              {yearOptions.map((y) => (
                <SelectItem key={y} value={y}>
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

        </div>

        <Tabs defaultValue="membri" className="space-y-4">
          <TabsList>
            <TabsTrigger value="membri">Membri</TabsTrigger>
            <TabsTrigger value="report">Report</TabsTrigger>
            <TabsTrigger value="impostazioni">Impostazioni</TabsTrigger>
          </TabsList>

          <TabsContent value="membri" className="space-y-4">
        <MembershipStats stats={stats} totalTesseramenti={totalTesseramenti} onRefresh={loadAll} />

        <div className="flex flex-col md:flex-row gap-2">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cerca nome, cognome, email o telefono..."
            className="flex-1"
          />
          <div className="flex gap-2">
            <Button onClick={() => openForm()} className="flex-1">
              <Plus className="mr-2 h-4 w-4" />
              Nuovo
            </Button>
            <Button onClick={exportExcel} disabled={!filtered.length} className="flex-1">
              <Download className="mr-2 h-4 w-4" />
              Esporta
            </Button>
            <Button onClick={exportManualMembers} className="flex-1" variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Esporta onorari
            </Button>
          </div>
        </div>
        <div className="flex flex-col md:flex-row gap-2 items-start md:items-center">
          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input
              type="checkbox"
              checked={showOnlyNotSent}
              onChange={(e) => setShowOnlyNotSent(e.target.checked)}
            />
            Solo senza tessera inviata
          </label>
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="md:max-w-xs">
              <SelectValue placeholder="Ordina per" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name_asc">Nome/Cognome (A-Z)</SelectItem>
              <SelectItem value="name_desc">Nome/Cognome (Z-A)</SelectItem>
              <SelectItem value="date_desc">Data iscrizione (recente)</SelectItem>
              <SelectItem value="date_asc">Data iscrizione (vecchia)</SelectItem>
              <SelectItem value="events_desc">Eventi partecipati (desc)</SelectItem>
              <SelectItem value="events_asc">Eventi partecipati (asc)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Card>
          <CardContent className="p-0 md:p-6">
            {loading ? (
              <div className="py-12 flex justify-center items-center">
                <Loader2 className="animate-spin h-8 w-8" />
              </div>
            ) : (
              <>
                {/* DESKTOP TABLE */}
                <div className="hidden md:block">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nome</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Data</TableHead>
                        <TableHead>Validità</TableHead>
                        <TableHead>Eventi</TableHead>
                        <TableHead>Tessera</TableHead>
                        <TableHead className="text-right">Azioni</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {paginatedMembers.map((m) => (
                        <TableRow key={m.id}>
                          <TableCell>
                            <div className="font-medium">
                              {m.name} {m.surname}
                            </div>
                            <div className="text-sm text-gray-400">{m.phone || "N/D"}</div>
                          </TableCell>
                          <TableCell>{m.email}</TableCell>
                          <TableCell>{formatDate(m.start_date)}</TableCell>
                          <TableCell>
                            {!m.subscription_valid || isExpired(m.end_date) ? (
                              <Badge variant="destructive">Scaduta</Badge>
                            ) : (
                              <Badge variant="success">{m.end_date}</Badge>
                            )}
                          </TableCell>
                          <TableCell>
                            {(m.attended_events || []).length}
                          </TableCell>
                          <TableCell>
                            <Badge variant={m.membership_sent ? "success" : "secondary"}>
                              {m.membership_sent ? "Inviata" : "Non inviata"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  onClick={() => router.push(routes.admin.membershipDetails(m.id))}
                                >
                                  <Eye className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Vedi Profilo</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button size="icon" variant="ghost" onClick={() => openForm(m)}>
                                  <Edit className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Modifica</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button size="icon" variant="ghost" onClick={() => sendCard(m.id)}>
                                  <Ticket className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Invia tessera</TooltipContent>
                            </Tooltip>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="text-red-500"
                                  onClick={() => remove(m.id)}
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </TooltipTrigger>
                              <TooltipContent>Elimina</TooltipContent>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {/* MOBILE CARDS */}
                <div className="block md:hidden space-y-4 p-4">
                  {paginatedMembers.map((m) => (
                    <Card key={m.id} className="bg-neutral-900 border-neutral-800">
                      <CardHeader className="flex flex-row items-start justify-between gap-4 p-4">
                        <div>
                          <h3 className="font-bold">
                            {m.name} {m.surname}
                          </h3>
                          <p className="text-sm text-gray-400">{m.email}</p>
                        </div>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-5 w-5" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => router.push(routes.admin.membershipDetails(m.id))}>

                              <Eye className="mr-2 h-4 w-4" /> Vedi Profilo
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openForm(m)}>
                              <Edit className="mr-2 h-4 w-4" /> Modifica
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => sendCard(m.id)}>
                              <Ticket className="mr-2 h-4 w-4" /> Invia Tessera
                            </DropdownMenuItem>
                            {m.wallet_url && (
                              <DropdownMenuItem onClick={() => window.open(m.wallet_url, "_blank")}>
                                <Wallet className="mr-2 h-4 w-4" /> Apri Wallet
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuItem onClick={() => remove(m.id)} className="text-red-500 focus:text-red-500">
                              <Trash2 className="mr-2 h-4 w-4" /> Elimina
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </CardHeader>
                      <CardContent className="p-4 pt-0 grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="font-semibold">Validità</p>
                          {!m.subscription_valid || isExpired(m.end_date) ? (
                            <Badge variant="destructive" className="mt-1">
                              Scaduta
                            </Badge>
                          ) : (
                            <Badge variant="success" className="mt-1">
                              {m.end_date}
                            </Badge>
                          )}
                        </div>
                        <div>
                          <p className="font-semibold">Eventi</p>
                          <Badge variant="secondary" className="mt-1">
                            {(m.attended_events || []).length}
                          </Badge>
                        </div>
                        <div>
                          <p className="font-semibold">Data</p>
                          <p className="text-sm text-gray-300">{formatDate(m.start_date)}</p>
                        </div>
                        <div>
                          <p className="font-semibold">Tessera</p>
                          <Badge variant={m.membership_sent ? "success" : "secondary"} className="mt-1">
                            {m.membership_sent ? "Inviata" : "Non inviata"}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </>
            )}
            {sortedMembers.length === 0 && !loading && (
              <div className="text-center py-12 text-gray-500">Nessun membro trovato.</div>
            )}
          </CardContent>
        </Card>

        {sortedMembers.length > 0 && !loading && (
          <div className="flex flex-col gap-3 px-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-gray-400">
              Mostrando <span className="text-white">{totalItems ? startIndex + 1 : 0}</span>–<span className="text-white">{endIndex}</span> di <span className="text-white">{totalItems}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-400">Righe per pagina</span>
              <select
                className="rounded border border-gray-700 bg-gray-800 px-2 py-1"
                value={pageSize}
                onChange={(e) => {
                  const nextPageSize = parseInt(e.target.value, 10) || 25
                  setPageSize(nextPageSize)
                  setPage(1)
                }}
              >
                {[10, 25, 50, 100].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setPage(1)} disabled={clampedPage <= 1}>
                «
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={clampedPage <= 1}>
                Prec
              </Button>
              <span className="text-sm text-gray-300">
                Pagina <span className="font-semibold text-white">{clampedPage}</span> / <span className="text-white">{totalPages}</span>
              </span>
              <Button variant="outline" size="sm" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={clampedPage >= totalPages}>
                Succ
              </Button>
              <Button variant="outline" size="sm" onClick={() => setPage(totalPages)} disabled={clampedPage >= totalPages}>
                »
              </Button>
            </div>
          </div>
        )}
          </TabsContent>

          <TabsContent value="report" className="space-y-4">
            <div className="flex flex-col md:flex-row gap-2 items-start md:items-center">
              <Select value={selectedEventId} onValueChange={setSelectedEventId}>
                <SelectTrigger className="md:max-w-md">
                  <SelectValue placeholder="Seleziona evento per export" />
                </SelectTrigger>
                <SelectContent>
                  {eventOptions.map((ev) => (
                    <SelectItem key={ev.id} value={ev.id}>
                      {eventOptionsMap[ev.id]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button onClick={exportEventExcel} disabled={!selectedEventId || exportEventLoading}>
                {exportEventLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Esportazione...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Esporta evento
                  </>
                )}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="impostazioni" className="space-y-4">
            <Tabs value={settingsTab} onValueChange={setSettingsTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2 max-w-xs">
                <TabsTrigger value="price">Prezzo</TabsTrigger>
                <TabsTrigger value="wallet">Wallet</TabsTrigger>
              </TabsList>

              <TabsContent value="price" className="space-y-4 pt-3">
                <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-4">
                  <p className="text-sm text-gray-400">Prezzo Membership ({selectedYear})</p>
                  <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
                    {priceEditing ? (
                      <>
                        <Input
                          type="number"
                          value={tempPrice}
                          onChange={(e) => setTempPrice(e.target.value)}
                          placeholder="€"
                          className="w-28"
                        />
                        <Button size="sm" onClick={onSavePrice}>Salva</Button>
                        <Button size="sm" variant="outline" onClick={() => setPriceEditing(false)}>Annulla</Button>
                      </>
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="text-xl font-semibold">
                          {membershipPrice && membershipPrice.year === selectedYear && membershipPrice.price != null
                            ? `${membershipPrice.price} €`
                            : "Non definito"}
                        </span>
                        <Button
                          size="icon"
                          variant="ghost"
                          disabled={isMembershipPriceReadOnly}
                          onClick={() => {
                            if (isMembershipPriceReadOnly) return
                            setTempPrice(
                              membershipPrice && membershipPrice.year === selectedYear && membershipPrice.price != null
                                ? membershipPrice.price.toString()
                                : ""
                            )
                            setPriceEditing(true)
                          }}
                        >
                          <Edit className="h-5 w-5" />
                        </Button>
                      </div>
                    )}
                  </div>
                  {isMembershipPriceReadOnly && (
                    <p className="mt-3 text-sm text-gray-400">
                      Valore letto da <code>NEXT_MEMBESHIP_PRICE</code>. Aggiorna il file .env per modificarlo.
                    </p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="wallet" className="space-y-4 pt-3">
                <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-4">
                  <p className="text-sm text-gray-400">Modello Wallet Pass2U</p>
                  <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
                    {walletModelEditing ? (
                      <>
                        <Input
                          value={tempWalletModel}
                          onChange={(e) => setTempWalletModel(e.target.value)}
                          placeholder="Model ID Pass2U"
                          className="w-full sm:w-72 font-mono text-sm"
                        />
                        <Button
                          size="sm"
                          onClick={async () => {
                            const ok = await saveWalletModel(tempWalletModel)
                            if (ok) {
                              setWalletModelEditing(false)
                              setWalletModelWarningOpen(false)
                            }
                          }}
                        >
                          Salva
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setWalletModelEditing(false)}>Annulla</Button>
                      </>
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm text-gray-300">
                          {walletModelId || <span className="text-gray-500 italic">Non configurato</span>}
                        </span>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            setTempWalletModel(walletModelId || "")
                            setWalletModelEditing(true)
                          }}
                        >
                          <Edit className="h-5 w-5" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </TabsContent>
        </Tabs>

        <Dialog
          open={settingsOpen}
          onOpenChange={(open) => {
            setSettingsOpen(open)
            if (!open) {
              setPriceEditing(false)
              setWalletModelEditing(false)
            }
          }}
        >
          <DialogContent className="sm:max-w-xl">
            <DialogHeader>
              <DialogTitle>Impostazioni Membership</DialogTitle>
              <DialogDescription>
                Configura prezzo annuale e modello Wallet senza occupare spazio nella pagina principale.
              </DialogDescription>
            </DialogHeader>

            <Tabs value={settingsTab} onValueChange={setSettingsTab} className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="price">Prezzo</TabsTrigger>
                <TabsTrigger value="wallet">Wallet</TabsTrigger>
              </TabsList>

              <TabsContent value="price" className="space-y-4 pt-3">
                <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-4">
                  <p className="text-sm text-gray-400">Prezzo Membership ({selectedYear})</p>
                  <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
                    {priceEditing ? (
                      <>
                        <Input
                          type="number"
                          value={tempPrice}
                          onChange={(e) => setTempPrice(e.target.value)}
                          placeholder="€"
                          className="w-28"
                        />
                        <Button size="sm" onClick={onSavePrice}>
                          Salva
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setPriceEditing(false)}>
                          Annulla
                        </Button>
                      </>
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="text-xl font-semibold">
                          {membershipPrice && membershipPrice.year === selectedYear && membershipPrice.price != null
                            ? `${membershipPrice.price} €`
                            : "Non definito"}
                        </span>
                        <Button
                          size="icon"
                          variant="ghost"
                          disabled={isMembershipPriceReadOnly}
                          onClick={() => {
                            if (isMembershipPriceReadOnly) return
                            setTempPrice(
                              membershipPrice && membershipPrice.year === selectedYear && membershipPrice.price != null
                                ? membershipPrice.price.toString()
                                : ""
                            )
                            setPriceEditing(true)
                          }}
                        >
                          <Edit className="h-5 w-5" />
                        </Button>
                      </div>
                    )}
                  </div>
                  {isMembershipPriceReadOnly && (
                    <p className="mt-3 text-sm text-gray-400">
                      Valore letto da <code>NEXT_MEMBESHIP_PRICE</code>. Aggiorna il file .env per modificarlo.
                    </p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="wallet" className="space-y-4 pt-3">
                <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-4">
                  <p className="text-sm text-gray-400">Modello Wallet Pass2U</p>
                  <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center">
                    {walletModelEditing ? (
                      <>
                        <Input
                          value={tempWalletModel}
                          onChange={(e) => setTempWalletModel(e.target.value)}
                          placeholder="Model ID Pass2U"
                          className="w-full sm:w-72 font-mono text-sm"
                        />
                        <Button
                          size="sm"
                          onClick={async () => {
                            const ok = await saveWalletModel(tempWalletModel)
                            if (ok) {
                              setWalletModelEditing(false)
                              setWalletModelWarningOpen(false)
                            }
                          }}
                        >
                          Salva
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setWalletModelEditing(false)}>
                          Annulla
                        </Button>
                      </>
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm text-gray-300">
                          {walletModelId || <span className="text-gray-500 italic">Non configurato</span>}
                        </span>
                        <Button
                          size="icon"
                          variant="ghost"
                          onClick={() => {
                            setTempWalletModel(walletModelId || "")
                            setWalletModelEditing(true)
                          }}
                        >
                          <Edit className="h-5 w-5" />
                        </Button>
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>

        <Dialog open={walletModelWarningOpen} onOpenChange={setWalletModelWarningOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2 text-amber-500">
                <AlertTriangle className="h-5 w-5" />
                Configurazione Wallet mancante
              </DialogTitle>
              <DialogDescription className="text-gray-300">
                {walletModelWarningText}
              </DialogDescription>
            </DialogHeader>
            <DialogFooter className="sm:justify-between">
              <Button variant="outline" onClick={() => setWalletModelWarningOpen(false)}>
                Chiudi
              </Button>
              <Button
                onClick={() => {
                  setWalletModelWarningOpen(false)
                  openSettings("wallet")
                }}
              >
                Apri impostazioni
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <MembershipModal
          isOpen={modalOpen}
          onClose={closeForm}
          form={form}
          isEditMode={editMode}
          loading={loading}
          onSubmit={submitForm}
          onInput={(e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))}
          onCheckbox={(name, val) => setForm((f) => ({ ...f, [name]: val }))}
        />
      </motion.div>
    </TooltipProvider>
  )
}
