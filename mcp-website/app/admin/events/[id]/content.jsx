"use client"

// Force SSR in Next.js (important for Firebase Hosting)

// Force SSR in Next.js (important for Firebase Hosting)

import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { routes } from "@/config/routes"

import {
  ArrowLeft,
  Plus,
  Send,
  Download,
  Eye,
  Ticket,
  Trash2,
  Loader2,
  Info,
  MapPin,
  Euro,
  BadgeIcon as IdCard,
  Users,
  StickyNote,
  X,
  FileText,
  Check,
  UserPlus,
  RefreshCw,
} from "lucide-react"
import { motion } from "framer-motion"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  CardDescription
} from "@/components/ui/card"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell
} from "@/components/ui/table"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"

import { useAdminEvents } from "@/hooks/useAdminEvents"
import { useAdminParticipants } from "@/hooks/useAdminParticipants"
import { getImageUrl, downloadStorageFile } from "@/config/firebaseStorage"
import { ParticipantModal } from "@/components/admin/participants/ParticipantModal"
import { LocationModal } from "@/components/admin/events/LocationModal"
import { EventStats } from "@/components/admin/events/EventStats"
import { exportParticipantsToExcel } from "@/lib/excel" // ✅ NUOVO IMPORT
import { resolvePurchaseMode } from "@/config/events-utils"
import { getMembershipPrice } from "@/services/admin/memberships"
import { generateScanToken as apiGenerateScanToken, verifyScanToken as apiVerifyScanToken, deactivateScanToken as apiDeactivateScanToken } from "@/services/admin/entrance"

function QuickAddDialog({ open, onOpenChange, onSubmit }) {
  const [form, setForm] = useState({ name: "", surname: "", email: "", birthdate: "" })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) setForm({ name: "", surname: "", email: "", birthdate: "" })
  }, [open])

  const handleBirthdateChange = (value) => {
    const cleaned = value.replace(/\D/g, "")
    let formatted = cleaned
    if (cleaned.length > 4) formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2, 4)}-${cleaned.slice(4, 8)}`
    else if (cleaned.length > 2) formatted = `${cleaned.slice(0, 2)}-${cleaned.slice(2)}`
    setForm((f) => ({ ...f, birthdate: formatted }))
  }

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try { await onSubmit(form); onOpenChange(false) } finally { setSaving(false) }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader><DialogTitle>Aggiunta rapida</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div><Label>Nome</Label><Input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required /></div>
          <div><Label>Cognome</Label><Input value={form.surname} onChange={(e) => setForm((f) => ({ ...f, surname: e.target.value }))} required /></div>
          <div><Label>Email</Label><Input type="email" value={form.email} onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} required /></div>
          <div>
            <Label>Data di nascita (gg-mm-aaaa)</Label>
            <Input type="text" placeholder="es. 30-08-1999" value={form.birthdate} onChange={(e) => handleBirthdateChange(e.target.value)} pattern="^\d{2}-\d{2}-\d{4}$" inputMode="numeric" required />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Annulla</Button>
            <Button type="submit" disabled={saving}>{saving ? <span className="flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin"/> Salva…</span> : "Salva"}</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function EventContent({ id: eventId }) {
  const router = useRouter()
  const { events, loading: evLoad, refreshEvents } = useAdminEvents()
  const {
    participants,
    loading: pLoad,
    loadAll,
    create,
    update,
    remove,
    sendLocation,
    sendLocationToAll,
    sendTicket,
    jobId,
    jobStatus,
    jobPercent,
    jobSent,
    jobFailed,
  } = useAdminParticipants(eventId)
  const isJobActive = jobStatus === "running" || jobStatus === "queued";
  const [event, setEvent] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [membershipPrice, setMembershipPrice] = useState(null)
  const filtersKey = `mcp_admin_participants_filters_${eventId || "unknown"}`
  const [search, setSearch] = useState("")
  const [genderFilter, setGenderFilter] = useState("all") // all | male | female | nd
  const [locationFilter, setLocationFilter] = useState("all") // all | yes | no
  const [memberFilter, setMemberFilter] = useState("all") // all | yes | no

  const [isParticipantModalOpen, setParticipantModalOpen] = useState(false)
  const [participantForm, setParticipantForm] = useState({})
  const [initialForm, setInitialForm] = useState(null)
  const [isEditMode, setEditMode] = useState(false)

  const [isLocationModalOpen, setLocationModalOpen] = useState(false)
  const [locationTargetName, setLocationTargetName] = useState("")
  const [selectedParticipantId, setSelectedParticipantId] = useState(null)
  const [address, setAddress] = useState("")
  const [link, setLink] = useState("")
  const [message, setMessage] = useState("")
  const [showJobProgress, setShowJobProgress] = useState(false)
  // Pagination
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(25)
  // Nuovo stato per sapere se la barra è stata chiusa definitivamente
  const [jobProgressDismissed, setJobProgressDismissed] = useState(false)

  // Checkin tab state
  const [checkinSearch, setCheckinSearch] = useState("")
  const [checkinOnlyMissing, setCheckinOnlyMissing] = useState(true)
  const [checkinQuickOpen, setCheckinQuickOpen] = useState(false)

  // Entrance / scan token state
  const [scanToken, setScanToken] = useState(null)
  const [scanUrl, setScanUrl] = useState(null)
  const [scanTokenExpiry, setScanTokenExpiry] = useState(null)
  const [scanTokenLoading, setScanTokenLoading] = useState(false)
  const [scanCopied, setScanCopied] = useState(false)

  useEffect(() => {
    loadAll()
  }, [eventId, loadAll])

  const filtersLoadedRef = useRef(false)
  useEffect(() => {
    if (!eventId || typeof window === "undefined") return
    if (filtersLoadedRef.current) return
    try {
      const stored = JSON.parse(window.localStorage.getItem(filtersKey) || "{}")
      if (stored.search != null) setSearch(stored.search)
      if (stored.genderFilter) setGenderFilter(stored.genderFilter)
      if (stored.locationFilter) setLocationFilter(stored.locationFilter)
      if (stored.memberFilter) setMemberFilter(stored.memberFilter)
      if (stored.pageSize) setPageSize(stored.pageSize)
    } catch {}
    filtersLoadedRef.current = true
  }, [eventId, filtersKey])

  useEffect(() => {
    if (!eventId || typeof window === "undefined") return
    const payload = {
      search,
      genderFilter,
      locationFilter,
      memberFilter,
      pageSize,
    }
    window.localStorage.setItem(filtersKey, JSON.stringify(payload))
  }, [eventId, filtersKey, search, genderFilter, locationFilter, memberFilter, pageSize])

  useEffect(() => {
    let isMounted = true
    getMembershipPrice()
      .then((res) => {
        if (!isMounted || res?.error) return
        setMembershipPrice(res)
      })
      .catch(() => {})
    return () => {
      isMounted = false
    }
  }, [])

  const targetEvent = useMemo(() => events.find((e) => e.id === eventId) || null, [events, eventId])

  const refreshRequestedRef = useRef(false)

  useEffect(() => {
    if (!targetEvent && !evLoad && !refreshRequestedRef.current) {
      refreshRequestedRef.current = true
      Promise.resolve(refreshEvents()).finally(() => {
        refreshRequestedRef.current = false
      })
    }
  }, [targetEvent, evLoad, refreshEvents])

  useEffect(() => {
    if (!targetEvent) return
    setEvent(targetEvent)
    if (targetEvent.image) {
      getImageUrl("events", `${targetEvent.image}.jpg`)
        .then((url) => {
          if (url) setImageUrl(url)
        })
        .catch(console.error)
    } else {
      setImageUrl(null)
    }
  }, [targetEvent])

  // reset page when filters/search change or dataset changes
  useEffect(() => {
    setPage(1)
  }, [search, genderFilter, locationFilter, memberFilter, participants.length])

  const visibleCols = [
    { key: "name", label: "Nome e Cognome" },
    { key: "birthdate", label: "Data Nascita" },
    { key: "gender", label: "Genere" },
    { key: "price", label: "Prezzo (€)" },
    { key: "createdAt", label: "Data Acquisto" },
    { key: "payment_method", label: "Metodo" },
    { key: "membershipId", label: "Membro", badge: true },
    { key: "location_sent", label: "Posizione", badge: true },
    { key: "ticket_sent", label: "Biglietto", badge: true },
    { key: "ticket_pdf_url", label: "Scarica" },
    { key: "purchase_id", label: "Acquisto" },
  ]

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return participants.filter((p) => {
      // search by name+surname
      const matchSearch = `${p.name} ${p.surname}`.toLowerCase().includes(q)

      // gender normalization
      const g = (p.gender || "nd").toLowerCase()
      const normGender = g === "male" || g === "maschio" ? "male" : g === "female" || g === "femmina" ? "female" : "nd"
      const matchGender = genderFilter === "all" || normGender === genderFilter

      // location sent filter
      const loc = !!p.location_sent
      const matchLocation = locationFilter === "all" || (locationFilter === "yes" ? loc : !loc)

      // member filter (solo membershipId determina se è membro)
      const isMember = !!p.membershipId
      const matchMember = memberFilter === "all" || (memberFilter === "yes" ? isMember : !isMember)

      return matchSearch && matchGender && matchLocation && matchMember
    })
  }, [participants, search, genderFilter, locationFilter, memberFilter])

  const filteredCount = filtered.length

  const sorted = useMemo(() => [...filtered].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)), [filtered])

  const stats = useMemo(
    () => ({
      total: participants.length,
      new24h: participants.filter((p) => new Date(p.createdAt) >= Date.now() - 86400000).length,
    }),
    [participants],
  )

  // Derived pagination
  const totalItems = sorted.length
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
  const clampedPage = Math.min(page, totalPages)
  const startIndex = (clampedPage - 1) * pageSize
  const endIndex = Math.min(startIndex + pageSize, totalItems)
  const pageRows = sorted.slice(startIndex, endIndex)

  // Checkin computed data
  const checkinCounters = useMemo(() => {
    const total = participants.length
    const entered = participants.filter((p) => !!p.entered).length
    return { total, entered, missing: total - entered }
  }, [participants])

  const checkinNormalized = useMemo(() => {
    const q = checkinSearch.trim().toLowerCase()
    let list = participants
      .map((p) => ({ ...p, _key: `${(p.name || "").toLowerCase()} ${(p.surname || "").toLowerCase()}`.trim() }))
      .filter((p) => (q ? p._key.includes(q) : true))
    if (checkinOnlyMissing) list = list.filter((p) => p.entered !== true)
    return list.sort((a, b) => {
      if (!!a.entered !== !!b.entered) return a.entered ? 1 : -1
      return `${a.surname || ""} ${a.name || ""}`.toLowerCase().localeCompare(`${b.surname || ""} ${b.name || ""}`.toLowerCase())
    })
  }, [participants, checkinSearch, checkinOnlyMissing])

  const checkinMarkEntered = useCallback(async (p, value = true) => {
    try { await update(p.id, { entered: !!value, entered_at: new Date().toISOString() }) } catch {}
  }, [update])

  const checkinQuickAdd = useCallback(async ({ name, surname, email, birthdate }) => {
    try {
      await create({ name, surname, email, birthdate, phone: "", price: event?.price ?? null, ticket_sent: false, location_sent: false, purchase_id: null, source: "door" })
      setCheckinQuickOpen(false)
    } catch {}
  }, [create, event?.price])

  // Entrance: load stored token from localStorage on mount
  useEffect(() => {
    if (!eventId || typeof window === "undefined") return
    const stored = (() => { try { return JSON.parse(localStorage.getItem(`mcp_scan_token_${eventId}`) || "null") } catch { return null } })()
    if (!stored) return
    const expiry = stored.expires_at ? new Date(stored.expires_at) : null
    if (expiry && expiry < new Date()) { localStorage.removeItem(`mcp_scan_token_${eventId}`); return }
    setScanToken(stored.token)
    setScanUrl(stored.scan_url)
    setScanTokenExpiry(expiry)
  }, [eventId])

  const buildScanUrl = (tok) =>
    typeof window !== "undefined"
      ? `${window.location.origin}/scan/${tok}`
      : `https://musiconnectingpeople.com/scan/${tok}`

  const handleGenerateScanToken = async () => {
    setScanTokenLoading(true)
    const res = await apiGenerateScanToken(eventId)
    setScanTokenLoading(false)
    if (res?.error) return
    const expiry = new Date(Date.now() + 12 * 60 * 60 * 1000)
    const url = buildScanUrl(res.token)
    setScanToken(res.token)
    setScanUrl(url)
    setScanTokenExpiry(expiry)
    if (typeof window !== "undefined") {
      localStorage.setItem(`mcp_scan_token_${eventId}`, JSON.stringify({ token: res.token, scan_url: url, expires_at: expiry.toISOString() }))
    }
  }

  const handleCopyScanUrl = async () => {
    if (!scanUrl) return
    try { await navigator.clipboard.writeText(scanUrl) } catch { }
    setScanCopied(true)
    setTimeout(() => setScanCopied(false), 2000)
  }

  const handleShareScanUrl = async () => {
    if (!scanUrl) return
    if (navigator.share) { try { await navigator.share({ url: scanUrl }) } catch { } }
    else { handleCopyScanUrl() }
  }

  const handleDeactivateScanToken = async () => {
    if (!scanToken) return
    setScanTokenLoading(true)
    await apiDeactivateScanToken(scanToken)
    setScanTokenLoading(false)
    setScanToken(null)
    setScanUrl(null)
    setScanTokenExpiry(null)
    if (typeof window !== "undefined") localStorage.removeItem(`mcp_scan_token_${eventId}`)
  }

  const formatScanExpiry = (d) => {
    if (!d) return ""
    return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" })
  }

  // ✅ Nuova versione export
  const exportToExcel = () => {
    exportParticipantsToExcel(sorted, event?.title, eventId)
  }

  const exportToTxt = () => {
    if (!participants.length) return

    const alphabetical = [...participants].sort((a, b) => {
      const aKey = `${(a.surname || "").toLowerCase()} ${(a.name || "").toLowerCase()}`
      const bKey = `${(b.surname || "").toLowerCase()} ${(b.name || "").toLowerCase()}`
      return aKey.localeCompare(bKey)
    })

    const lines = alphabetical.map((p) => {
      const priceNum = Number(p.price)
      const isFree = !Number.isNaN(priceNum) && priceNum === 0
      const displayName = `${p.name || ""} ${p.surname || ""}`.trim() || `Partecipante`
      return `${displayName}${isFree ? " - OMAGGIO" : ""}`
    })

    const content = lines.join("\n")
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    const safeTitle = event?.title ? event.title.replace(/\s+/g, "_").toLowerCase() : "evento"
    link.download = `partecipanti_${safeTitle}_${eventId}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const openParticipantModal = (p = null) => {
    if (p) {
      setEditMode(true)
      setParticipantForm({ ...p })
      setInitialForm({ ...p })
    } else {
      setEditMode(false)
      setParticipantForm({
        name: "",
        surname: "",
        email: "",
        phone: "",
        birthdate: "",
        gender: "",
        price: "",
        payment_method: "cash",
        membership_included: false,
        send_ticket_on_create: false,
      })
      setInitialForm(null)
    }
    setParticipantModalOpen(true)
  }

  const closeParticipantModal = () => {
    setParticipantModalOpen(false)
    setParticipantForm({})
    setInitialForm(null)
    setEditMode(false)
  }

  const handleParticipantSubmit = async (e) => {
    e.preventDefault()
    try {
      if (isEditMode) {
        const diff = {}
        Object.keys(participantForm).forEach((k) => {
          if (participantForm[k] !== initialForm[k]) diff[k] = participantForm[k]
        })
        if (Object.keys(diff).length) {
          await update(participantForm.id, { ...diff })
        }
      } else {
        await create(participantForm)
      }
      closeParticipantModal()
    } catch (err) {
      console.error(err)
    }
  }

  const openLocationModalForAll = () => {
    setMessage("")
    setLocationModalOpen(true)
    setLocationTargetName(null)
  }

  const openLocationModalForOne = (p) => {
    setMessage("")
    setLocationModalOpen(true)
    setLocationTargetName(`${p.name} ${p.surname}`)
    setSelectedParticipantId(p.id)
  }

  const handleSendLocation = async ({ address, link, message }) => {
    if (locationTargetName) {
      await sendLocation(selectedParticipantId, { address, link, message })
    } else {
      setJobProgressDismissed(false)
      setShowJobProgress(true)
      await sendLocationToAll({ address, link, message })
    }
    setLocationModalOpen(false)
  }

  // Mostra di nuovo la barra di avanzamento a fine job se non è stata chiusa definitivamente
  useEffect(() => {
    if (jobStatus && (jobStatus === "completed" || jobStatus === "failed") && !jobProgressDismissed) {
      setShowJobProgress(true)
    }
  }, [jobStatus, jobProgressDismissed])

  const purchaseMode = resolvePurchaseMode(event)
  const eventStatus = event?.status || "active"
  const eventDateObj = useMemo(() => {
    if (!event?.date) return null
    const [d, m, y] = event.date.split("-").map(Number)
    const parsed = new Date(y, (m || 1) - 1, d || 1)
    return isNaN(parsed.getTime()) ? null : parsed
  }, [event?.date])
  const isPastEvent = useMemo(() => {
    if (!eventDateObj) return false
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    return eventDateObj < today
  }, [eventDateObj])

  if (evLoad || !event) {
    return (
      <div className="flex items-center justify-center h-screen text-white">
        <Loader2 className="animate-spin h-8 w-8" />
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="text-gray-50 min-h-screen p-6 lg:p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-7xl mx-auto space-y-6"
        >
          <Button variant="ghost" onClick={() => router.push(routes.admin.events)}>
            <ArrowLeft className="h-4 w-4 mr-2" /> Torna agli eventi
          </Button>

          <div>
            <h1 className="text-4xl font-bold">{event.title}</h1>
            <p className="text-gray-400">
              {event.date} • {event.startTime}
            </p>
          </div>

          {/* Event card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {imageUrl && <img src={imageUrl || "/placeholder.svg"} className="w-full object-cover rounded-lg" />}
            <Card className="bg-zinc-900 text-white p-6 shadow-xl border border-zinc-700 rounded-xl">
              <CardHeader>
                <CardTitle className="text-xl font-bold flex items-center gap-3 border-b border-zinc-700 pb-3 mb-5">
                  Dettagli evento
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-5 text-base leading-relaxed">
                <p className="flex items-center gap-3">
                  <MapPin size={20} />
                  <strong>Luogo:</strong> {event.location}
                </p>
                <p className="flex items-center gap-3">
                  <Euro size={20} />
                  <strong>Prezzo:</strong> {event.price ?? "N/A"} €
                </p>
                {event.fee && (
                  <p className="flex items-center gap-3">
                    <Euro size={20} />
                    <strong>Fee:</strong> {event.fee} €
                  </p>
                )}
                <p className="flex items-center gap-3">
                  <IdCard size={20} />
                  <strong>Tessera:</strong>{" "}
                  {membershipPrice?.price != null ? `${membershipPrice.price} €` : "N/A"}
                  {membershipPrice?.year ? ` (${membershipPrice.year})` : ""}
                </p>
                <p className="flex items-center gap-3">
                  <Info size={20} />
                  <strong>Purchase mode:</strong> {purchaseMode}
                </p>
                <div className="flex items-center gap-3">
                  <Users size={20} />
                  <strong>Stato:</strong>
                  <Badge variant={eventStatus === "active" ? "success" : "secondary"} className="text-sm px-2 py-0.5">
                    {eventStatus === "coming_soon" && "Coming soon"}
                    {eventStatus === "sold_out" && "Sold out"}
                    {eventStatus === "ended" && "Terminato"}
                    {eventStatus === "active" && "Attivo"}
                  </Badge>
                </div>

                {/* Lineup centrato e grande */}
                <div className="mt-8 text-center">
                  <p className="text-2xl font-bold mb-3 flex justify-center items-center gap-2">
                    <Users size={22} /> Lineup
                  </p>
                    <ul className="space-y-1 text-lg text-zinc-100">
                    {(event.lineup || []).map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>

                {/* Note centrato e grande */}
                <div className="mt-10 text-center text-zinc-400 italic mt-6">
                  <p className="text-xl flex items-center justify-center gap-2">
                    <StickyNote size={20} /> <strong>Note:</strong>
                  </p>
                  <p className="mt-2 text-sm">{event.note || "-"}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {(eventStatus !== "active" || isPastEvent) && (
            <div className="rounded-xl border border-zinc-700 bg-zinc-900/70 p-4 text-center">
              <p className="text-lg font-semibold text-white">
                {eventStatus === "sold_out"
                  ? "Evento sold out"
                  : eventStatus === "coming_soon"
                    ? "Evento in arrivo"
                    : "Evento terminato"}
              </p>
              <p className="text-sm text-gray-400">
                {eventStatus === "sold_out"
                  ? "Capienza massima raggiunta. Puoi comunque gestire i partecipanti e le statistiche."
                  : eventStatus === "coming_soon"
                    ? "L’evento non è ancora attivo. Aggiorna lo stato quando sarà pronto per la vendita."
                    : "Questo evento è già stato completato. Puoi comunque gestire i partecipanti e le statistiche."}
              </p>
            </div>
          )}

          <Tabs defaultValue="partecipanti">
            <TabsList>
              <TabsTrigger value="partecipanti">Partecipanti</TabsTrigger>
              <TabsTrigger value="statistiche">Statistiche</TabsTrigger>
              <TabsTrigger value="ingresso">In the event</TabsTrigger>
            </TabsList>

            <TabsContent value="statistiche">
              <EventStats participants={participants} onRefresh={loadAll} />
            </TabsContent>

            <TabsContent value="partecipanti">
          {/* Participants */}
          <Card>
            <CardHeader className="gap-3">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Partecipanti ({filteredCount} / {stats.total})</CardTitle>
                  <CardDescription>Lista & azioni</CardDescription>
                </div>
              </div>
              {/* Search — full width */}
              <input
                className="px-3 py-2 bg-gray-800 border border-gray-700 rounded w-full"
                placeholder="Cerca partecipante..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              {/* Filters — 3 cols on mobile, inline on desktop */}
              <div className="grid grid-cols-3 sm:flex gap-2">
                <select
                  className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm"
                  value={genderFilter}
                  onChange={(e) => setGenderFilter(e.target.value)}
                  aria-label="Filtra per genere"
                >
                  <option value="all">Genere: tutti</option>
                  <option value="male">Maschio</option>
                  <option value="female">Femmina</option>
                  <option value="nd">N/D</option>
                </select>
                <select
                  className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm"
                  value={locationFilter}
                  onChange={(e) => setLocationFilter(e.target.value)}
                  aria-label="Filtra per location inviata"
                >
                  <option value="all">Location: tutte</option>
                  <option value="yes">Inviata</option>
                  <option value="no">Non inviata</option>
                </select>
                <select
                  className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm"
                  value={memberFilter}
                  onChange={(e) => setMemberFilter(e.target.value)}
                  aria-label="Filtra per membro"
                >
                  <option value="all">Membro: tutti</option>
                  <option value="yes">Sì</option>
                  <option value="no">No</option>
                </select>
              </div>
              {/* Actions — 2 cols on mobile, inline on desktop */}
              <div className="grid grid-cols-2 sm:flex gap-2">
                <Button onClick={() => openParticipantModal()}>
                  <Plus className="mr-2 h-4 w-4" /> Aggiungi
                </Button>
                <Button onClick={() => openLocationModalForAll("tutti")}>
                  <Send className="mr-2 h-4 w-4" /> Location
                </Button>
                <Button onClick={exportToExcel} disabled={!sorted.length}>
                  <Download className="mr-2 h-4 w-4" /> Esporta
                </Button>
                <Button onClick={exportToTxt} disabled={!participants.length}>
                  <FileText className="mr-2 h-4 w-4" /> TXT
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {pLoad && !isJobActive ? (
                <Table>
                  <TableBody>
                    <TableRow>
                      <TableCell colSpan={visibleCols.length + 2} className="py-12 text-center">
                        <Loader2 className="animate-spin h-8 w-8 mx-auto" />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                      <TableHead className="text-center">Modifica</TableHead>
                      {visibleCols.map((c) => (
                        <TableHead key={c.key}>{c.label}</TableHead>
                      ))}
                      <TableHead className="text-center">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                        {pageRows.map((p) => (
                          <TableRow key={p.id}>
                            <TableCell className="text-center">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button variant="ghost" size="icon" onClick={() => openParticipantModal(p)}>
                                    <Eye className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Modifica</TooltipContent>
                              </Tooltip>
                            </TableCell>

                            <TableCell>
                              {p.name} {p.surname}
                            </TableCell>
                            <TableCell>{p.birthdate || "-"}</TableCell>
                            <TableCell>
                              {p.gender === "male" ? (
                                <Badge variant="outline" className="bg-blue-900/20 text-blue-300 border-blue-600">
                                  Maschio
                                </Badge>
                              ) : p.gender === "female" ? (
                                <Badge variant="outline" className="bg-pink-900/20 text-pink-300 border-pink-600">
                                  Femmina
                                </Badge>
                              ) : (
                                <Badge variant="secondary" className="bg-gray-700 text-gray-300">
                                  N/A
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell>{p.price ?? "-"}</TableCell>
                            <TableCell>{p.createdAt || "-"}</TableCell>
                            <TableCell>{p.payment_method || p.paymentMethod || "-"}</TableCell>
                            {/* Badge Membro cliccabile */}
                            <TableCell className="text-center">
                              {p.membershipId ? (
                                <Button
                                  variant="link"
                                  onClick={() => router.push(routes.admin.membershipDetails(p.membershipId))}                                >
                                  <Badge variant="success" className="p-2">
                                    Membro
                                  </Badge>
                                </Button>
                              ) : (
                                <Badge variant="secondary" className="p-2">
                                  No
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant={p.location_sent ? "success" : "secondary"}>
                                {p.location_sent ? "Inviata" : "No"}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Badge variant={p.ticket_sent ? "success" : "secondary"}>
                                {p.ticket_sent ? "Inviato" : "No"}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-center">
                              <Button
                                variant="link"
                                size="icon"
                                onClick={() => p.ticket_pdf_url && downloadStorageFile(p.ticket_pdf_url)}
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            </TableCell>
                            {/* Colonna Acquisto */}
                            <TableCell className="text-center">
                              {p.purchase_id ? (
                              <Button
                                size="sm"
                                onClick={() => {
                                  router.push(routes.admin.purchasesDetails(p.purchase_id));
                                }}
                              >
                                Vai
                              </Button>
                              ) : (
                                "-"
                              )}
                            </TableCell>
                            <TableCell className="text-right space-x-1 whitespace-nowrap">
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => {
                                      setParticipantForm(p)
                                      openLocationModalForOne(p)
                                    }}
                                  >
                                    <MapPin className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Invia Location</TooltipContent>
                              </Tooltip>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button variant="ghost" size="icon" onClick={() => sendTicket(p.id)}>
                                    <Ticket className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Invia Biglietto</TooltipContent>
                              </Tooltip>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button variant="destructive" size="icon" onClick={() => remove(p.id)}>
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Elimina</TooltipContent>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        ))}
                        {pageRows.length === 0 && (
                          <TableRow>
                            <TableCell colSpan={visibleCols.length + 2} className="text-center py-12">
                              Nessun partecipante.
                            </TableCell>
                          </TableRow>
                        )}
                      </TableBody>
                    </Table>
                  </div>
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4 px-2">
                    <div className="text-sm text-gray-400">
                      Mostrando <span className="text-white">{totalItems ? startIndex + 1 : 0}</span>–<span className="text-white">{endIndex}</span> di <span className="text-white">{totalItems}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-400">Righe per pagina</span>
                      <select
                        className="px-2 py-1 bg-gray-800 border border-gray-700 rounded"
                        value={pageSize}
                        onChange={(e) => {
                          const n = parseInt(e.target.value, 10) || 25
                          setPageSize(n)
                          setPage(1)
                        }}
                      >
                        {[10, 25, 50, 100].map((n) => (
                          <option key={n} value={n}>{n}</option>
                        ))}
                      </select>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={() => setPage(1)} disabled={clampedPage <= 1}>«</Button>
                      <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={clampedPage <= 1}>Prec</Button>
                      <span className="text-sm text-gray-300">
                        Pagina <span className="font-semibold text-white">{clampedPage}</span> / <span className="text-white">{totalPages}</span>
                      </span>
                      <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={clampedPage >= totalPages}>Succ</Button>
                      <Button variant="outline" size="sm" onClick={() => setPage(totalPages)} disabled={clampedPage >= totalPages}>»</Button>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
            </TabsContent>

            {/* ── In the event (check-in) ── */}
            <TabsContent value="ingresso" className="space-y-4">
              {/* Scan token panel */}
              <Card className="bg-zinc-900 border-zinc-700">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Ingresso</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {!scanUrl ? (
                    <Button onClick={handleGenerateScanToken} disabled={scanTokenLoading}>
                      {scanTokenLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Genera link scanner
                    </Button>
                  ) : (
                    <>
                      <div className="flex items-center gap-2 text-emerald-400 text-sm">
                        <Check className="h-4 w-4 shrink-0" />
                        <span>Link attivo · scade alle {formatScanExpiry(scanTokenExpiry)}</span>
                      </div>
                      <div className="text-xs font-mono text-gray-300 break-all bg-zinc-800 rounded px-3 py-2">{scanUrl}</div>
                      <div className="flex flex-wrap gap-2">
                        <Button size="sm" onClick={handleCopyScanUrl} variant={scanCopied ? "secondary" : "outline"}>
                          {scanCopied ? "Copiato!" : "Copia link"}
                        </Button>
                        <Button size="sm" onClick={handleShareScanUrl} variant="outline">Condividi</Button>
                        <Button size="sm" variant="destructive" onClick={handleDeactivateScanToken} disabled={scanTokenLoading}>
                          {scanTokenLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                          Disattiva
                        </Button>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Counters */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-zinc-900 rounded-md p-3 text-center">
                  <div className="text-xs text-gray-400">Entrati</div>
                  <div className="text-2xl font-bold text-emerald-400">{checkinCounters.entered}</div>
                </div>
                <div className="bg-zinc-900 rounded-md p-3 text-center">
                  <div className="text-xs text-gray-400">Mancanti</div>
                  <div className="text-2xl font-bold text-yellow-400">{checkinCounters.missing}</div>
                </div>
                <div className="bg-zinc-900 rounded-md p-3 text-center">
                  <div className="text-xs text-gray-400">Totale</div>
                  <div className="text-2xl font-bold text-blue-400">{checkinCounters.total}</div>
                </div>
              </div>

              {/* Search + filter + actions */}
              <div className="flex flex-col sm:flex-row gap-2">
                <Input
                  placeholder="Cerca per nome e cognome…"
                  value={checkinSearch}
                  onChange={(e) => setCheckinSearch(e.target.value)}
                  className="h-10 bg-zinc-900 border-zinc-700 flex-1"
                />
                <div className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    id="only-missing-toggle"
                    type="checkbox"
                    checked={checkinOnlyMissing}
                    onChange={(e) => setCheckinOnlyMissing(e.target.checked)}
                  />
                  <Label htmlFor="only-missing-toggle" className="cursor-pointer">Solo mancanti</Label>
                </div>
                <div className="grid grid-cols-2 sm:flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => loadAll()}>
                    <RefreshCw className="h-4 w-4 mr-2"/> Aggiorna
                  </Button>
                  <Button size="sm" onClick={() => setCheckinQuickOpen(true)}>
                    <UserPlus className="h-4 w-4 mr-2"/> Aggiungi
                  </Button>
                </div>
              </div>

              {/* List */}
              <div className="bg-zinc-900/60 rounded-lg border border-zinc-800">
                <div className="divide-y divide-zinc-800">
                  {pLoad ? (
                    <div className="flex justify-center items-center py-12">
                      <Loader2 className="animate-spin h-6 w-6 mr-2"/> Caricamento…
                    </div>
                  ) : checkinNormalized.length === 0 ? (
                    <div className="text-center py-12 text-gray-400">Nessun risultato</div>
                  ) : (
                    checkinNormalized.map((p) => (
                      <div key={p.id} className="flex items-center justify-between gap-2 p-3">
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          <div className={`w-2.5 h-2.5 shrink-0 rounded-full ${p.entered ? "bg-emerald-500" : "bg-yellow-500"}`}/>
                          <div className="min-w-0">
                            <div className="font-medium truncate">{p.name} {p.surname}</div>
                            <div className="text-xs text-gray-400 truncate">{p.email}</div>
                            {p.birthdate && <div className="text-xs text-gray-400">DN: {p.birthdate}</div>}
                          </div>
                          <div className="shrink-0">
                            {p.membershipId ? (
                              <Badge variant="success">Membro</Badge>
                            ) : (
                              <Badge variant="secondary">No</Badge>
                            )}
                          </div>
                        </div>
                        <div className="shrink-0">
                          {p.entered ? (
                            <Button variant="outline" size="sm" onClick={() => checkinMarkEntered(p, false)}>Annulla</Button>
                          ) : (
                            <Button size="sm" onClick={() => checkinMarkEntered(p, true)}>
                              <Check className="h-4 w-4 mr-1"/> Entra
                            </Button>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
              <QuickAddDialog open={checkinQuickOpen} onOpenChange={setCheckinQuickOpen} onSubmit={checkinQuickAdd} />
            </TabsContent>
          </Tabs>
        </motion.div>

        {/* Modali */}
        <ParticipantModal
          isOpen={isParticipantModalOpen}
          onClose={closeParticipantModal}
          form={participantForm}
          isEditMode={isEditMode}
          onSubmit={handleParticipantSubmit}
          onInput={(e) =>
            setParticipantForm((f) => ({
              ...f,
              [e.target.name]: e.target.name === "gender" ? e.target.value.toLowerCase() : e.target.value,
            }))
          }
          onCheckbox={(name, value) => setParticipantForm((f) => ({ ...f, [name]: value }))}
        />

        <LocationModal
          isOpen={isLocationModalOpen}
          onClose={() => setLocationModalOpen(false)}
          targetName={locationTargetName}
          address={address}
          setAddress={setAddress}
          link={link}
          setLink={setLink}
          message={message}
          setMessage={setMessage}
          onSubmit={handleSendLocation}
        />
      </div>
      {showJobProgress && jobStatus && jobStatus !== "idle" && (
        <div className="fixed bottom-4 right-4 z-50 w-80">
          <Card className="bg-zinc-900 text-white shadow-xl border border-zinc-700">
            <CardHeader className="pb-2 flex items-start justify-between">
              <div>
                <CardTitle className="text-base">Invio location</CardTitle>
                <CardDescription className="text-xs">
                  Stato: {jobStatus} • Inviate: {jobSent} • Errori: {jobFailed}
                </CardDescription>
              </div>
              {/* Pulsante X per nascondere/chiudere sempre */}
              <Button
                size="icon"
                variant="ghost"
                onClick={() => {
                  setShowJobProgress(false)
                  setJobProgressDismissed(true)
                }}
              >
                <X className="h-4 w-4" />
              </Button>
            </CardHeader>

            <CardContent>
              <div className="w-full h-2 rounded bg-zinc-800 overflow-hidden">
                <div
                  className="h-2 bg-primary transition-all"
                  style={{ width: `${jobPercent || 0}%` }}
                />
              </div>

              <div className="mt-2 flex items-center justify-between text-xs text-zinc-400">
                <span>{jobPercent || 0}%</span>
                <div className="flex items-center gap-2">
                  {(jobStatus === "running" || jobStatus === "queued") && (
                    <span>Invio in corso…</span>
                  )}
                  {/* Pulsante per nascondere durante l’invio o chiudere a fine job */}
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 px-2"
                    onClick={() => {
                      if (jobStatus === "completed" || jobStatus === "failed") {
                        setJobProgressDismissed(true)
                      }
                      setShowJobProgress(false)
                    }}
                  >
                    {(jobStatus === "completed" || jobStatus === "failed") ? "Chiudi" : "Nascondi"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </TooltipProvider>
  )
}
