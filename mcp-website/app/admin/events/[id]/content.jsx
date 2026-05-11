"use client"

// Force SSR in Next.js (important for Firebase Hosting)

// Force SSR in Next.js (important for Firebase Hosting)

import { useState, useEffect, useMemo, useRef, useCallback } from "react"
import { useRouter } from "next/navigation"
import { routes } from "@/config/routes"

import {
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
  Tag,
} from "lucide-react"
import { motion } from "framer-motion"

import { Button } from "@/components/ui/button"
import { AdminLoading, AdminPageHeader } from "@/components/admin/AdminPageChrome"
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
import { getMembershipPrice, getMemberships } from "@/services/admin/memberships"
import { endpoints } from "@/config/endpoints"
import { safeFetch } from "@/lib/fetch"

const ADMIN_THEME = {
  "--color-black": "#0a0a0a",
  "--color-surface": "#111111",
  "--color-border": "#1e1e1e",
  "--color-muted": "#3a3a3a",
  "--color-white": "#ffffff",
  "--color-off": "#b0b0b0",
  "--color-orange": "#e8820c",
  "--color-purple": "#511a6c",
  "--color-red": "#e8241a",
  "--color-yellow": "#f0d44a",
}
const TITLE_FONT = '"Helvetica Neue", Helvetica, Arial, sans-serif'
import { generateScanToken as apiGenerateScanToken, verifyScanToken as apiVerifyScanToken, deactivateScanToken as apiDeactivateScanToken, manualEntry as apiManualEntry } from "@/services/admin/entrance"
import { listDiscountCodes } from "@/services/admin/discountCodes"
import { getAllPurchases } from "@/services/admin/purchases"

function parseMembershipDate(value) {
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

function getMembershipYear(membership) {
  const startDate = parseMembershipDate(membership?.start_date)
  if (startDate) {
    return startDate.getFullYear().toString()
  }

  const endDate = parseMembershipDate(membership?.end_date)
  if (endDate) {
    const isFirstDayOfYear = endDate.getDate() === 1 && endDate.getMonth() === 0
    const year = isFirstDayOfYear ? endDate.getFullYear() - 1 : endDate.getFullYear()
    return year.toString()
  }

  return null
}

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
    sendOmaggioEmails,
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
  const [paymentFilter, setPaymentFilter] = useState("all") // all | cash | iban | private_paypal | website
  const [riduzioneFilter, setRiduzioneFilter] = useState("all") // all | yes | no

  // Omaggio state
  const [omaggioSearch, setOmaggioSearch] = useState("")
  const [omaggioEntryTime, setOmaggioEntryTime] = useState("")
  const [omaggioSending, setOmaggioSending] = useState(false)
  const [omaggioRowSendingId, setOmaggioRowSendingId] = useState(null)
  const [omaggioResult, setOmaggioResult] = useState(null)
  const [omaggioPage, setOmaggioPage] = useState(1)

  const [isParticipantModalOpen, setParticipantModalOpen] = useState(false)
  const [participantForm, setParticipantForm] = useState({})
  const [initialForm, setInitialForm] = useState(null)
  const [isEditMode, setEditMode] = useState(false)

  const [isLocationModalOpen, setLocationModalOpen] = useState(false)
  const [locationTargetName, setLocationTargetName] = useState("")
  const [selectedParticipantId, setSelectedParticipantId] = useState(null)
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
  const currentMembershipYear = useMemo(() => new Date().getFullYear().toString(), [])
  const [currentYearMemberships, setCurrentYearMemberships] = useState([])
  const [membershipsLoading, setMembershipsLoading] = useState(false)
  const [discountCodes, setDiscountCodes] = useState([])
  const [discountPurchases, setDiscountPurchases] = useState([])

  // Event Guide state
  const [guidePublished, setGuidePublished] = useState(false)
  const [guideSections, setGuideSections] = useState([])
  const [guideSaving, setGuideSaving] = useState(false)
  const [guideToast, setGuideToast] = useState("")
  const [guideTogglingPublished, setGuideTogglingPublished] = useState(false)
  const [guideDragOver, setGuideDragOver] = useState(null)
  const [guideLoading, setGuideLoading] = useState(false)

  // Location (Posizione) state
  const [locationData, setLocationData] = useState({ label: "", maps_url: "", maps_embed_url: "", address: "", message: "" })
  const [locationPublished, setLocationPublished] = useState(false)
  const [locationSaving, setLocationSaving] = useState(false)
  const [locationTogglingPublished, setLocationTogglingPublished] = useState(false)
  const [locationToast, setLocationToast] = useState("")
  const [locationLoading, setLocationLoading] = useState(false)

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
      if (stored.paymentFilter) setPaymentFilter(stored.paymentFilter)
      if (stored.riduzioneFilter) setRiduzioneFilter(stored.riduzioneFilter)
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
      paymentFilter,
      riduzioneFilter,
      pageSize,
    }
    window.localStorage.setItem(filtersKey, JSON.stringify(payload))
  }, [eventId, filtersKey, search, genderFilter, locationFilter, memberFilter, paymentFilter, riduzioneFilter, pageSize])

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

  const loadCurrentYearMemberships = useCallback(async () => {
    setMembershipsLoading(true)
    try {
      const res = await getMemberships()
      if (!Array.isArray(res) || res?.error) {
        setCurrentYearMemberships([])
        return
      }

      const filtered = res
        .filter((m) => getMembershipYear(m) === currentMembershipYear)
        .map((m) => ({
          id: m.id,
          name: m.name || "",
          surname: m.surname || "",
          email: m.email || "",
          phone: m.phone || "",
          birthdate: m.birthdate || "",
        }))
        .sort((a, b) =>
          `${a.surname} ${a.name}`.toLowerCase().localeCompare(`${b.surname} ${b.name}`.toLowerCase())
        )

      setCurrentYearMemberships(filtered)
    } catch {
      setCurrentYearMemberships([])
    } finally {
      setMembershipsLoading(false)
    }
  }, [currentMembershipYear])

  useEffect(() => {
    loadCurrentYearMemberships()
  }, [loadCurrentYearMemberships])

  useEffect(() => {
    let isMounted = true
    async function loadDiscountSummary() {
      if (!eventId) return
      const [codesRes, purchasesRes] = await Promise.all([
        listDiscountCodes(eventId),
        getAllPurchases(),
      ])
      if (!isMounted) return
      setDiscountCodes(Array.isArray(codesRes) ? codesRes : [])
      setDiscountPurchases(
        Array.isArray(purchasesRes)
          ? purchasesRes.filter((purchase) => (purchase.ref_id || purchase.event_id) === eventId && (purchase.discountCodeId || purchase.discount_code_id))
          : []
      )
    }
    loadDiscountSummary()
    return () => {
      isMounted = false
    }
  }, [eventId])

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

  useEffect(() => {
    if (!eventId) return
    let isMounted = true
    setGuideLoading(true)
    safeFetch(`${endpoints.admin.events.getGuide}?event_id=${eventId}`, "GET")
      .then((data) => {
        if (!isMounted || data?.error) return
        setGuidePublished(!!data.published)
        setGuideSections(Array.isArray(data.sections) ? data.sections : [])
      })
      .catch(() => {})
      .finally(() => { if (isMounted) setGuideLoading(false) })
    return () => { isMounted = false }
  }, [eventId])

  useEffect(() => {
    if (!eventId) return
    let isMounted = true
    setLocationLoading(true)
    safeFetch(`${endpoints.admin.events.getLocation}?event_id=${eventId}`, "GET")
      .then((data) => {
        if (!isMounted || data?.error) return
        setLocationData({
          label: data.label || "",
          maps_url: data.maps_url || "",
          maps_embed_url: data.maps_embed_url || "",
          address: data.address || "",
          message: data.message || "",
        })
        setLocationPublished(!!data.published)
      })
      .catch(() => {})
      .finally(() => { if (isMounted) setLocationLoading(false) })
    return () => { isMounted = false }
  }, [eventId])

  // reset page when filters/search change or dataset changes
  useEffect(() => {
    setPage(1)
  }, [search, genderFilter, locationFilter, memberFilter, paymentFilter, riduzioneFilter, participants.length])

  useEffect(() => {
    setOmaggioPage(1)
  }, [omaggioSearch, participants.length])

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

  // Separate omaggi from regular participants
  const omaggioParticipants = useMemo(
    () => participants.filter((p) => (p.payment_method || p.paymentMethod || "").toLowerCase() === "omaggio"),
    [participants]
  )
  const regularParticipants = useMemo(
    () => participants.filter((p) => (p.payment_method || p.paymentMethod || "").toLowerCase() !== "omaggio"),
    [participants]
  )

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return regularParticipants.filter((p) => {
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

      // payment method filter
      const pm = (p.payment_method || p.paymentMethod || "").toLowerCase()
      const matchPayment = paymentFilter === "all" || pm === paymentFilter

      // riduzione filter
      const isRiduzione = !!p.riduzione
      const matchRiduzione = riduzioneFilter === "all" || (riduzioneFilter === "yes" ? isRiduzione : !isRiduzione)

      return matchSearch && matchGender && matchLocation && matchMember && matchPayment && matchRiduzione
    })
  }, [regularParticipants, search, genderFilter, locationFilter, memberFilter, paymentFilter, riduzioneFilter])

  const filteredOmaggi = useMemo(() => {
    const q = omaggioSearch.toLowerCase()
    return omaggioParticipants.filter((p) =>
      `${p.name} ${p.surname}`.toLowerCase().includes(q)
    )
  }, [omaggioParticipants, omaggioSearch])

  const omaggioUnsentCount = useMemo(
    () => omaggioParticipants.filter((p) => !p.omaggio_email_sent).length,
    [omaggioParticipants]
  )

  const filteredCount = filtered.length

  const sorted = useMemo(() => [...filtered].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)), [filtered])

  const sortedOmaggi = useMemo(() => [...filteredOmaggi].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)), [filteredOmaggi])

  const stats = useMemo(
    () => ({
      total: participants.length,
      new24h: participants.filter((p) => new Date(p.createdAt) >= Date.now() - 86400000).length,
    }),
    [participants],
  )

  const discountSummary = useMemo(() => {
    const active = discountCodes.filter((code) => Boolean(code.isActive ?? code.is_active)).length
    const used = discountCodes.reduce((sum, code) => sum + Number(code.usedCount ?? code.used_count ?? 0), 0)
    const discountTotal = discountPurchases.reduce((sum, purchase) => sum + Number(purchase.discountAmount ?? purchase.discount_amount ?? 0), 0)
    return { active, used, discountTotal }
  }, [discountCodes, discountPurchases])

  // Derived pagination (regular)
  const totalItems = sorted.length
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize))
  const clampedPage = Math.min(page, totalPages)
  const startIndex = (clampedPage - 1) * pageSize
  const endIndex = Math.min(startIndex + pageSize, totalItems)
  const pageRows = sorted.slice(startIndex, endIndex)

  // Omaggio pagination
  const omaggioPageSize = 25
  const omaggioTotalItems = sortedOmaggi.length
  const omaggioTotalPages = Math.max(1, Math.ceil(omaggioTotalItems / omaggioPageSize))
  const omaggioClampedPage = Math.min(omaggioPage, omaggioTotalPages)
  const omaggioStartIndex = (omaggioClampedPage - 1) * omaggioPageSize
  const omaggioEndIndex = Math.min(omaggioStartIndex + omaggioPageSize, omaggioTotalItems)
  const omaggioPageRows = sortedOmaggi.slice(omaggioStartIndex, omaggioEndIndex)

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
    try {
      if (p.membershipId) {
        const res = await apiManualEntry(eventId, p.membershipId, !!value)
        if (res?.error) return
        await loadAll()
        return
      }
      await update(p.id, { entered: !!value, entered_at: value ? new Date().toISOString() : null })
    } catch {}
  }, [update, eventId, loadAll])

  const checkinQuickAdd = useCallback(async ({ name, surname, email, birthdate }) => {
    try {
      await create({ name, surname, email, birthdate, phone: "", price: event?.price ?? null, ticket_sent: false, location_sent: false, purchase_id: null, source: "door" })
      setCheckinQuickOpen(false)
    } catch {}
  }, [create, event?.price])

  // Entrance: load stored token from localStorage on mount
  useEffect(() => {
    if (!eventId || typeof window === "undefined") return
    let mounted = true

    const run = async () => {
      const storageKey = `mcp_scan_token_${eventId}`
      const stored = (() => {
        try { return JSON.parse(localStorage.getItem(storageKey) || "null") } catch { return null }
      })()
      if (!stored) return

      const expiry = stored.expires_at ? new Date(stored.expires_at) : null
      if (expiry && expiry < new Date()) {
        localStorage.removeItem(storageKey)
        return
      }

      const verify = await apiVerifyScanToken(stored.token)
      if (verify?.error || verify?.valid !== true) {
        localStorage.removeItem(storageKey)
        if (!mounted) return
        setScanToken(null)
        setScanUrl(null)
        setScanTokenExpiry(null)
        return
      }

      if (!mounted) return
      setScanToken(stored.token)
      setScanUrl(stored.scan_url)
      setScanTokenExpiry(expiry)
    }

    run()
    return () => { mounted = false }
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
    const res = await apiDeactivateScanToken(scanToken)
    setScanTokenLoading(false)
    const clearLocalToken = () => {
      setScanToken(null)
      setScanUrl(null)
      setScanTokenExpiry(null)
      if (typeof window !== "undefined") localStorage.removeItem(`mcp_scan_token_${eventId}`)
    }

    if (!res?.error) {
      clearLocalToken()
      return
    }

    // Robustness: if transport failed but backend actually processed deactivation,
    // verify current token status and reconcile local UI state.
    const verify = await apiVerifyScanToken(scanToken)
    if (verify?.valid === false && ["inactive", "expired", "not_found"].includes(verify?.reason)) {
      clearLocalToken()
      return
    }
  }

  const formatScanExpiry = (d) => {
    if (!d) return ""
    return d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" })
  }

  // ✅ Nuova versione export
  const exportToExcel = () => {
    exportParticipantsToExcel(sorted, event?.title, eventId)
  }

  const exportOmaggioToExcel = () => {
    exportParticipantsToExcel(sortedOmaggi, event?.title ? `${event.title} - Omaggi` : "Omaggi", eventId)
  }

  const downloadTxt = (list, filename) => {
    if (!list.length) return
    const alphabetical = [...list].sort((a, b) => {
      const aKey = `${(a.surname || "").toLowerCase()} ${(a.name || "").toLowerCase()}`
      const bKey = `${(b.surname || "").toLowerCase()} ${(b.name || "").toLowerCase()}`
      return aKey.localeCompare(bKey)
    })
    const lines = alphabetical.map((p) => `${p.name || ""} ${p.surname || ""}`.trim() || "Partecipante")
    const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const safeEventTitle = event?.title ? event.title.replace(/\s+/g, "_").toLowerCase() : "evento"

  const exportToTxt = () => {
    downloadTxt(regularParticipants, `partecipanti_${safeEventTitle}_${eventId}.txt`)
  }

  const exportOmaggioTxt = () => {
    downloadTxt(omaggioParticipants, `omaggi_${safeEventTitle}_${eventId}.txt`)
  }

  const exportRiduzioneTxt = () => {
    const riduzione = regularParticipants.filter((p) => !!p.riduzione)
    downloadTxt(riduzione, `riduzione_${safeEventTitle}_${eventId}.txt`)
  }

  const handleSendOmaggioEmails = async () => {
    setOmaggioSending(true)
    setOmaggioResult(null)
    const res = await sendOmaggioEmails(omaggioEntryTime || null, { skipAlreadySent: true })
    setOmaggioResult(res || null)
    setOmaggioSending(false)
  }

  const handleSendSingleOmaggioEmail = async (participantId) => {
    if (!participantId) return
    setOmaggioRowSendingId(participantId)
    setOmaggioResult(null)
    const res = await sendOmaggioEmails(omaggioEntryTime || null, {
      participantId,
      skipAlreadySent: false,
    })
    setOmaggioResult(res || null)
    setOmaggioRowSendingId(null)
  }

  const openParticipantModal = (p = null) => {
    if (p) {
      const membershipId = p.membership_id ?? p.membershipId ?? null
      setEditMode(true)
      const normalized = { ...p, membership_id: membershipId, membershipId }
      setParticipantForm(normalized)
      setInitialForm(normalized)
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
        membership_id: null,
        send_ticket_on_create: false,
      })
      setInitialForm(null)
    }
    setParticipantModalOpen(true)
  }

  const openOmaggioModal = () => {
    setEditMode(false)
    setParticipantForm({
      name: "",
      surname: "",
      email: "musiconnectingpeople.to@gmail.com",
      phone: "",
      birthdate: "01-01-2000",
      gender: "",
      price: 0,
      payment_method: "omaggio",
      membership_included: false,
      membership_id: null,
      send_ticket_on_create: false,
      riduzione: false,
    })
    setInitialForm(null)
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

  const handleSendLocation = async ({ message }) => {
    if (locationTargetName) {
      await sendLocation(selectedParticipantId, { message })
    } else {
      setJobProgressDismissed(false)
      setShowJobProgress(true)
      await sendLocationToAll({ message })
    }
    setLocationModalOpen(false)
  }

  const handleSendLocationToAllFromTab = async () => {
    setJobProgressDismissed(false)
    setShowJobProgress(true)
    await sendLocationToAll({ message: locationData.message || undefined })
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
    return <AdminLoading label="Caricamento evento..." />
  }

  return (
    <TooltipProvider>
      <div className="min-h-screen p-6 lg:p-8" style={ADMIN_THEME}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-7xl mx-auto space-y-6"
        >
          <AdminPageHeader
            title={event.title}
            description={`${event.date} • ${event.startTime}`}
            backHref={routes.admin.events}
            backLabel="Torna agli eventi"
          />

          {/* Event card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {imageUrl && <img src={imageUrl || "/placeholder.svg"} className="w-full object-cover" />}
            <Card className="border-[var(--color-border)] bg-[var(--color-surface)] rounded-none">
              <CardHeader>
                <CardTitle className="text-base uppercase tracking-wide flex items-center gap-3 border-b border-[var(--color-border)] pb-3 mb-3" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>
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

          <Card className="bg-zinc-900 border-zinc-700 text-white">
            <CardContent className="p-5 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-3">
                <Tag className="h-5 w-5 text-mcp-orange" />
                <div>
                  <p className="font-semibold">Codici Sconto</p>
                  <p className="text-sm text-gray-400">
                    {discountSummary.active} attivi / {discountSummary.used} utilizzi totali / {discountSummary.discountTotal.toFixed(2)} € erogati
                  </p>
                </div>
              </div>
              <Button onClick={() => router.push(routes.admin.eventDiscountCodes(eventId))}>
                Gestisci codici
              </Button>
            </CardContent>
          </Card>

          {(eventStatus !== "active" || isPastEvent) && (
            <div className="border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-center">
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
              <TabsTrigger value="omaggi">Omaggi</TabsTrigger>
              <TabsTrigger value="statistiche">Statistiche</TabsTrigger>
              <TabsTrigger value="ingresso">In the event</TabsTrigger>
              <TabsTrigger value="posizione">Posizione</TabsTrigger>
              <TabsTrigger value="guide">Event Guide</TabsTrigger>
            </TabsList>

            <TabsContent value="statistiche">
              <EventStats participants={participants} onRefresh={loadAll} />
            </TabsContent>

            <TabsContent value="partecipanti" className="space-y-6">
              {/* ── Partecipanti (non-omaggio) ── */}
              <Card>
                <CardHeader className="gap-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Partecipanti ({filteredCount} / {regularParticipants.length})</CardTitle>
                      <CardDescription>Lista & azioni — esclusi gli omaggi</CardDescription>
                    </div>
                  </div>
                  <input
                    className="px-3 py-2 bg-gray-800 border border-gray-700 rounded w-full"
                    placeholder="Cerca partecipante..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                  {/* Filters */}
                  <div className="grid grid-cols-3 sm:flex gap-2 flex-wrap">
                    <select className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm" value={genderFilter} onChange={(e) => setGenderFilter(e.target.value)} aria-label="Filtra per genere">
                      <option value="all">Genere: tutti</option>
                      <option value="male">Maschio</option>
                      <option value="female">Femmina</option>
                      <option value="nd">N/D</option>
                    </select>
                    <select className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm" value={locationFilter} onChange={(e) => setLocationFilter(e.target.value)} aria-label="Filtra per location">
                      <option value="all">Location: tutte</option>
                      <option value="yes">Inviata</option>
                      <option value="no">Non inviata</option>
                    </select>
                    <select className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm" value={memberFilter} onChange={(e) => setMemberFilter(e.target.value)} aria-label="Filtra per membro">
                      <option value="all">Membro: tutti</option>
                      <option value="yes">Sì</option>
                      <option value="no">No</option>
                    </select>
                    <select className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm" value={paymentFilter} onChange={(e) => setPaymentFilter(e.target.value)} aria-label="Filtra per pagamento">
                      <option value="all">Pagamento: tutti</option>
                      <option value="cash">Cash</option>
                      <option value="iban">IBAN</option>
                      <option value="private_paypal">PayPal privato</option>
                      <option value="website">Website</option>
                    </select>
                    <select className="px-2 py-2 bg-gray-800 border border-gray-700 rounded text-sm" value={riduzioneFilter} onChange={(e) => setRiduzioneFilter(e.target.value)} aria-label="Filtra per riduzione">
                      <option value="all">Riduzione: tutti</option>
                      <option value="yes">Con riduzione</option>
                      <option value="no">Senza riduzione</option>
                    </select>
                  </div>
                  {/* Actions */}
                  <div className="grid grid-cols-2 sm:flex gap-2 flex-wrap">
                    <Button onClick={() => openParticipantModal()}><Plus className="mr-2 h-4 w-4" /> Aggiungi</Button>
                    <Button onClick={() => openLocationModalForAll("tutti")}><Send className="mr-2 h-4 w-4" /> Location</Button>
                    <Button onClick={exportToExcel} disabled={!sorted.length}><Download className="mr-2 h-4 w-4" /> Esporta</Button>
                    <Button onClick={exportToTxt} disabled={!regularParticipants.length}><FileText className="mr-2 h-4 w-4" /> TXT</Button>
                    <Button variant="outline" onClick={exportRiduzioneTxt} disabled={!regularParticipants.filter(p => !!p.riduzione).length}>
                      <FileText className="mr-2 h-4 w-4" /> TXT Riduzione
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {pLoad && !isJobActive ? (
                    <Table><TableBody><TableRow><TableCell colSpan={visibleCols.length + 3} className="py-12 text-center"><Loader2 className="animate-spin h-8 w-8 mx-auto" /></TableCell></TableRow></TableBody></Table>
                  ) : (
                    <>
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-center">Modifica</TableHead>
                              {visibleCols.map((c) => <TableHead key={c.key}>{c.label}</TableHead>)}
                              <TableHead>Riduzione</TableHead>
                              <TableHead className="text-center">Azioni</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {pageRows.map((p) => (
                              <TableRow key={p.id}>
                                <TableCell className="text-center">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" onClick={() => openParticipantModal(p)}><Eye className="h-4 w-4" /></Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Modifica</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                                <TableCell>{p.name} {p.surname}</TableCell>
                                <TableCell>{p.birthdate || "-"}</TableCell>
                                <TableCell>
                                  {p.gender === "male" ? <Badge variant="outline" className="bg-blue-900/20 text-blue-300 border-blue-600">Maschio</Badge>
                                    : p.gender === "female" ? <Badge variant="outline" className="bg-pink-900/20 text-pink-300 border-pink-600">Femmina</Badge>
                                    : <Badge variant="secondary" className="bg-gray-700 text-gray-300">N/A</Badge>}
                                </TableCell>
                                <TableCell>{p.price ?? "-"}</TableCell>
                                <TableCell>{p.createdAt || "-"}</TableCell>
                                <TableCell>{p.payment_method || p.paymentMethod || "-"}</TableCell>
                                <TableCell className="text-center">
                                  {p.membershipId ? (
                                    <Button variant="link" onClick={() => router.push(routes.admin.membershipDetails(p.membershipId))}>
                                      <Badge variant="success" className="p-2">Membro</Badge>
                                    </Button>
                                  ) : <Badge variant="secondary" className="p-2">No</Badge>}
                                </TableCell>
                                <TableCell className="text-center">
                                  <Badge variant={p.location_sent ? "success" : "secondary"}>{p.location_sent ? "Inviata" : "No"}</Badge>
                                </TableCell>
                                <TableCell className="text-center">
                                  <Badge variant={p.ticket_sent ? "success" : "secondary"}>{p.ticket_sent ? "Inviato" : "No"}</Badge>
                                </TableCell>
                                <TableCell className="text-center">
                                  <Button variant="link" size="icon" onClick={() => p.ticket_pdf_url && downloadStorageFile(p.ticket_pdf_url)}>
                                    <Download className="h-4 w-4" />
                                  </Button>
                                </TableCell>
                                <TableCell className="text-center">
                                  {p.purchase_id ? <Button size="sm" onClick={() => router.push(routes.admin.purchasesDetails(p.purchase_id))}>Vai</Button> : "-"}
                                </TableCell>
                                {/* Riduzione badge */}
                                <TableCell className="text-center">
                                  {p.riduzione ? <Badge variant="outline" className="bg-yellow-900/20 text-yellow-300 border-yellow-600">Riduzione</Badge> : <span className="text-gray-600">—</span>}
                                </TableCell>
                                <TableCell className="text-right space-x-1 whitespace-nowrap">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" onClick={() => { setParticipantForm(p); openLocationModalForOne(p) }}><MapPin className="h-4 w-4" /></Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Invia Location</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" onClick={() => sendTicket(p.id)}><Ticket className="h-4 w-4" /></Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Invia Biglietto</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="destructive" size="icon" onClick={() => remove(p.id)}><Trash2 className="h-4 w-4" /></Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Elimina</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                              </TableRow>
                            ))}
                            {pageRows.length === 0 && (
                              <TableRow><TableCell colSpan={visibleCols.length + 3} className="text-center py-12">Nessun partecipante.</TableCell></TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </div>
                      {/* Pagination */}
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mt-4 px-2">
                        <div className="text-sm text-gray-400">
                          Mostrando <span className="text-white">{totalItems ? startIndex + 1 : 0}</span>–<span className="text-white">{endIndex}</span> di <span className="text-white">{totalItems}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm text-gray-400">Righe per pagina</span>
                          <select className="px-2 py-1 bg-gray-800 border border-gray-700 rounded" value={pageSize} onChange={(e) => { setPageSize(parseInt(e.target.value, 10) || 25); setPage(1) }}>
                            {[10, 25, 50, 100].map((n) => <option key={n} value={n}>{n}</option>)}
                          </select>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button variant="outline" size="sm" onClick={() => setPage(1)} disabled={clampedPage <= 1}>«</Button>
                          <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={clampedPage <= 1}>Prec</Button>
                          <span className="text-sm text-gray-300">Pagina <span className="font-semibold text-white">{clampedPage}</span> / <span className="text-white">{totalPages}</span></span>
                          <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={clampedPage >= totalPages}>Succ</Button>
                          <Button variant="outline" size="sm" onClick={() => setPage(totalPages)} disabled={clampedPage >= totalPages}>»</Button>
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

            </TabsContent>

            {/* ── Omaggi ── */}
            <TabsContent value="omaggi" className="space-y-6">
              <Card>
                <CardHeader className="gap-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>Omaggi ({filteredOmaggi.length} / {omaggioParticipants.length})</CardTitle>
                      <CardDescription>Partecipanti con ingresso gratuito</CardDescription>
                    </div>
                  </div>
                  <input
                    className="px-3 py-2 bg-gray-800 border border-gray-700 rounded w-full"
                    placeholder="Cerca omaggio..."
                    value={omaggioSearch}
                    onChange={(e) => setOmaggioSearch(e.target.value)}
                  />
                  {/* Send omaggio email panel */}
                  <div className="flex flex-col sm:flex-row gap-2 items-start sm:items-center border border-zinc-700 rounded-lg p-3 bg-zinc-900/50">
                    <div className="flex flex-col gap-1 flex-1">
                      <Label htmlFor="omaggio-time" className="text-xs text-gray-400">Orario di entrata (es. 22:00)</Label>
                      <Input
                        id="omaggio-time"
                        placeholder="es. 22:00"
                        value={omaggioEntryTime}
                        onChange={(e) => setOmaggioEntryTime(e.target.value)}
                        className="h-9 w-40 bg-gray-800 border-gray-700"
                      />
                    </div>
                    <Button
                      onClick={handleSendOmaggioEmails}
                      disabled={omaggioSending || omaggioUnsentCount === 0}
                      className="mt-4 sm:mt-0 self-end"
                    >
                      {omaggioSending
                        ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Invio…</>
                        : <><Send className="mr-2 h-4 w-4" /> Invia email omaggi (non inviati)</>}
                    </Button>
                    {omaggioResult && (
                      <span className="text-sm text-gray-300 self-end">
                        Inviati: {omaggioResult.sent} / {omaggioResult.total}
                        {omaggioResult.skipped > 0 && ` · Skippati: ${omaggioResult.skipped}`}
                        {omaggioResult.failed > 0 && ` · Errori: ${omaggioResult.failed}`}
                      </span>
                    )}
                  </div>
                  {/* Actions */}
                  <div className="flex gap-2 flex-wrap">
                    <Button onClick={openOmaggioModal}><Plus className="mr-2 h-4 w-4" /> Aggiungi omaggio</Button>
                    <Button onClick={exportOmaggioToExcel} disabled={!omaggioParticipants.length}><Download className="mr-2 h-4 w-4" /> Esporta</Button>
                    <Button onClick={exportOmaggioTxt} disabled={!omaggioParticipants.length}><FileText className="mr-2 h-4 w-4" /> TXT Omaggi</Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {pLoad ? (
                    <Table><TableBody><TableRow><TableCell colSpan={9} className="py-12 text-center"><Loader2 className="animate-spin h-8 w-8 mx-auto" /></TableCell></TableRow></TableBody></Table>
                  ) : (
                    <>
                      <div className="overflow-x-auto">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="text-center">Modifica</TableHead>
                              <TableHead>Nome e Cognome</TableHead>
                              <TableHead>Data Nascita</TableHead>
                              <TableHead>Genere</TableHead>
                              <TableHead>Email</TableHead>
                              <TableHead>Data Aggiunta</TableHead>
                              <TableHead className="text-center">Email Omaggio</TableHead>
                              <TableHead className="text-center">Membro</TableHead>
                              <TableHead className="text-center">Azioni</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {omaggioPageRows.map((p) => (
                              <TableRow key={p.id}>
                                <TableCell className="text-center">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" onClick={() => openParticipantModal(p)}><Eye className="h-4 w-4" /></Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Modifica</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                                <TableCell>{p.name} {p.surname}</TableCell>
                                <TableCell>{p.birthdate || "-"}</TableCell>
                                <TableCell>
                                  {p.gender === "male" ? <Badge variant="outline" className="bg-blue-900/20 text-blue-300 border-blue-600">Maschio</Badge>
                                    : p.gender === "female" ? <Badge variant="outline" className="bg-pink-900/20 text-pink-300 border-pink-600">Femmina</Badge>
                                    : <Badge variant="secondary" className="bg-gray-700 text-gray-300">N/A</Badge>}
                                </TableCell>
                                <TableCell>{p.email || "-"}</TableCell>
                                <TableCell>{p.createdAt || "-"}</TableCell>
                                <TableCell className="text-center">
                                  <Badge variant={p.omaggio_email_sent ? "success" : "secondary"}>
                                    {p.omaggio_email_sent ? "Inviata" : "Non inviata"}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-center">
                                  {p.membershipId ? (
                                    <Button variant="link" onClick={() => router.push(routes.admin.membershipDetails(p.membershipId))}>
                                      <Badge variant="success" className="p-2">Membro</Badge>
                                    </Button>
                                  ) : <Badge variant="secondary" className="p-2">No</Badge>}
                                </TableCell>
                                <TableCell className="text-right space-x-1 whitespace-nowrap">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="ghost" size="icon" onClick={() => { setParticipantForm(p); openLocationModalForOne(p) }}><MapPin className="h-4 w-4" /></Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Invia Location</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        variant="ghost"
                                        size="icon"
                                        disabled={!p.email || omaggioRowSendingId === p.id}
                                        onClick={() => handleSendSingleOmaggioEmail(p.id)}
                                      >
                                        {omaggioRowSendingId === p.id
                                          ? <Loader2 className="h-4 w-4 animate-spin" />
                                          : <Send className="h-4 w-4" />}
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>{p.omaggio_email_sent ? "Reinvia email omaggio" : "Invia email omaggio"}</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button variant="destructive" size="icon" onClick={() => remove(p.id)}><Trash2 className="h-4 w-4" /></Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Elimina</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                              </TableRow>
                            ))}
                            {omaggioPageRows.length === 0 && (
                              <TableRow><TableCell colSpan={9} className="text-center py-12">Nessun omaggio.</TableCell></TableRow>
                            )}
                          </TableBody>
                        </Table>
                      </div>
                      {/* Omaggio pagination */}
                      {omaggioTotalItems > omaggioPageSize && (
                        <div className="flex items-center justify-end gap-2 mt-4 px-2">
                          <Button variant="outline" size="sm" onClick={() => setOmaggioPage(1)} disabled={omaggioClampedPage <= 1}>«</Button>
                          <Button variant="outline" size="sm" onClick={() => setOmaggioPage((p) => Math.max(1, p - 1))} disabled={omaggioClampedPage <= 1}>Prec</Button>
                          <span className="text-sm text-gray-300">Pagina <span className="font-semibold text-white">{omaggioClampedPage}</span> / <span className="text-white">{omaggioTotalPages}</span></span>
                          <Button variant="outline" size="sm" onClick={() => setOmaggioPage((p) => Math.min(omaggioTotalPages, p + 1))} disabled={omaggioClampedPage >= omaggioTotalPages}>Succ</Button>
                          <Button variant="outline" size="sm" onClick={() => setOmaggioPage(omaggioTotalPages)} disabled={omaggioClampedPage >= omaggioTotalPages}>»</Button>
                        </div>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* ── In the event (check-in) ── */}
            <TabsContent value="ingresso" className="space-y-4">
              {/* Scan token panel */}
              <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)]">
                <CardHeader className="pb-3 border-b border-[var(--color-border)]">
                  <CardTitle className="text-sm uppercase tracking-wide" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>Ingresso</CardTitle>
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
                <div className="border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-center">
                  <div className="text-xs uppercase tracking-wide text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>Entrati</div>
                  <div className="text-2xl font-bold text-emerald-400" style={{ fontFamily: TITLE_FONT }}>{checkinCounters.entered}</div>
                </div>
                <div className="border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-center">
                  <div className="text-xs uppercase tracking-wide text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>Mancanti</div>
                  <div className="text-2xl font-bold text-[var(--color-yellow)]" style={{ fontFamily: TITLE_FONT }}>{checkinCounters.missing}</div>
                </div>
                <div className="border border-[var(--color-border)] bg-[var(--color-surface)] p-3 text-center">
                  <div className="text-xs uppercase tracking-wide text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>Totale</div>
                  <div className="text-2xl font-bold text-[var(--color-orange)]" style={{ fontFamily: TITLE_FONT }}>{checkinCounters.total}</div>
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

            {/* ── Posizione ── */}
            <TabsContent value="posizione" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Posizione evento</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {locationLoading ? (
                    <div className="flex justify-center py-8"><Loader2 className="animate-spin h-6 w-6" /></div>
                  ) : (
                    <>
                      {/* Published toggle */}
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          id="location-published"
                          checked={locationPublished}
                          disabled={locationTogglingPublished}
                          onChange={async (e) => {
                            const next = e.target.checked
                            setLocationTogglingPublished(true)
                            const res = await safeFetch(endpoints.admin.events.toggleLocationPublished, "PATCH", {
                              event_id: eventId,
                              published: next,
                            })
                            setLocationTogglingPublished(false)
                            if (!res?.error) setLocationPublished(next)
                          }}
                          style={{ width: 18, height: 18, accentColor: "#e8820c" }}
                        />
                        <label htmlFor="location-published" className="text-sm cursor-pointer">
                          Location pubblicata (visibile ai membri)
                        </label>
                        {locationTogglingPublished && <Loader2 className="h-4 w-4 animate-spin text-orange-400" />}
                      </div>

                      {/* Fields */}
                      <div className="space-y-3">
                        <p className="text-xs uppercase tracking-widest text-orange-400 font-bold">Dati venue</p>
                        <div>
                          <Label className="text-xs text-gray-400 mb-1 block">Label venue (es. "Echi Club — Palermo")</Label>
                          <Input
                            value={locationData.label}
                            onChange={(e) => setLocationData((l) => ({ ...l, label: e.target.value }))}
                            placeholder="Nome venue — Città"
                          />
                        </div>
                        <div>
                          <Label className="text-xs text-gray-400 mb-1 block">Indirizzo preciso</Label>
                          <Input
                            value={locationData.address}
                            onChange={(e) => setLocationData((l) => ({ ...l, address: e.target.value }))}
                            placeholder="Via Roma 1, Palermo"
                          />
                        </div>
                        <div>
                          <Label className="text-xs text-gray-400 mb-1 block">Google Maps URL</Label>
                          <Input
                            value={locationData.maps_url}
                            onChange={(e) => setLocationData((l) => ({ ...l, maps_url: e.target.value }))}
                            placeholder="https://maps.google.com/?q=..."
                          />
                        </div>
                        <div>
                          <Label className="text-xs text-gray-400 mb-1 block">Google Maps Embed URL</Label>
                          <Input
                            value={locationData.maps_embed_url}
                            onChange={(e) => setLocationData((l) => ({ ...l, maps_embed_url: e.target.value }))}
                            placeholder="https://maps.google.com/maps?q=...&output=embed"
                          />
                        </div>
                        <div>
                          <Label className="text-xs text-gray-400 mb-1 block">Messaggio email (opzionale — usato nell&apos;invio)</Label>
                          <textarea
                            value={locationData.message}
                            onChange={(e) => setLocationData((l) => ({ ...l, message: e.target.value }))}
                            rows={3}
                            placeholder="Messaggio personalizzato per i partecipanti..."
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm resize-none"
                          />
                        </div>
                      </div>

                      {/* Save button */}
                      <div className="flex items-center gap-3 flex-wrap pt-1">
                        <Button
                          disabled={locationSaving}
                          onClick={async () => {
                            setLocationSaving(true)
                            setLocationToast("")
                            const res = await safeFetch(endpoints.admin.events.updateLocation, "PUT", {
                              event_id: eventId,
                              ...locationData,
                            })
                            setLocationSaving(false)
                            if (res?.error) {
                              setLocationToast(`Errore: ${res.error}`)
                            } else {
                              setLocationToast("Posizione salvata.")
                              if (res) setLocationPublished(!!res.published)
                            }
                            setTimeout(() => setLocationToast(""), 3000)
                          }}
                        >
                          {locationSaving ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Salvataggio…</> : "Salva posizione"}
                        </Button>
                        {locationToast && <span className="text-sm text-orange-400">{locationToast}</span>}
                      </div>

                      {/* Send to all */}
                      <div className="border border-zinc-700 rounded-lg p-4 bg-zinc-900/50 space-y-3">
                        <p className="text-xs uppercase tracking-widest text-orange-400 font-bold">Invio email location</p>
                        <p className="text-xs text-gray-400">
                          Invia la location a tutti i partecipanti che non l&apos;hanno ancora ricevuta.
                          Usa l&apos;indirizzo e il messaggio salvati sopra.
                        </p>
                        <Button
                          onClick={handleSendLocationToAllFromTab}
                          disabled={isJobActive || !locationData.address}
                        >
                          {isJobActive
                            ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Invio in corso…</>
                            : <><Send className="mr-2 h-4 w-4" /> Invia a tutti</>}
                        </Button>
                        {!locationData.address && (
                          <p className="text-xs text-yellow-400">Salva prima l&apos;indirizzo preciso per poter inviare.</p>
                        )}
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* ── Event Guide ── */}
            <TabsContent value="guide" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Event Guide</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Published toggle */}
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="guide-published"
                      checked={guidePublished}
                      disabled={guideTogglingPublished}
                      onChange={async (e) => {
                        const next = e.target.checked
                        setGuideTogglingPublished(true)
                        const res = await safeFetch(endpoints.admin.events.toggleGuidePublished, "PATCH", {
                          event_id: eventId,
                          published: next,
                        })
                        setGuideTogglingPublished(false)
                        if (!res?.error) {
                          setGuidePublished(next)
                        }
                      }}
                      style={{ width: 18, height: 18, accentColor: "#e8820c" }}
                    />
                    <label htmlFor="guide-published" className="text-sm cursor-pointer">
                      Guide pubblicata
                    </label>
                  </div>

                  {/* Sections */}
                  <div className="space-y-3">
                    <p className="text-xs uppercase tracking-widest text-orange-400 font-bold">Sezioni</p>
                    {guideSections.map((section, idx) => (
                      <div
                        key={section.id}
                        draggable
                        onDragStart={() => setGuideDragOver(idx)}
                        onDragOver={(e) => { e.preventDefault(); setGuideDragOver(idx) }}
                        onDrop={(e) => {
                          e.preventDefault()
                          setGuideSections((prev) => {
                            const from = prev.findIndex((s) => s.id === prev[guideDragOver]?.id)
                            if (from === -1 || from === idx) return prev
                            const next = [...prev]
                            const [moved] = next.splice(from, 1)
                            next.splice(idx, 0, moved)
                            return next.map((s, i) => ({ ...s, order: i }))
                          })
                          setGuideDragOver(null)
                        }}
                        className="bg-gray-900 border border-gray-700 rounded p-3 space-y-2"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500 cursor-grab select-none">⠿</span>
                          <select
                            value={section.type}
                            onChange={(e) => setGuideSections((prev) => prev.map((s, i) => i === idx ? { ...s, type: e.target.value } : s))}
                            className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-sm flex-shrink-0"
                          >
                            <option value="text">Testo</option>
                            <option value="how_to_reach">Come arrivare</option>
                            <option value="info">Info</option>
                            <option value="warning">Avviso</option>
                            <option value="checklist">Checklist</option>
                          </select>
                          <div className="flex items-center gap-1 ml-auto">
                            <label className="text-xs text-gray-400 flex items-center gap-1 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={section.visible !== false}
                                onChange={(e) => setGuideSections((prev) => prev.map((s, i) => i === idx ? { ...s, visible: e.target.checked } : s))}
                                style={{ accentColor: "#e8820c" }}
                              />
                              Visibile
                            </label>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-300 ml-2 h-7 px-2"
                              onClick={() => setGuideSections((prev) => prev.filter((_, i) => i !== idx).map((s, i) => ({ ...s, order: i })))}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                        <Input
                          value={section.title}
                          onChange={(e) => setGuideSections((prev) => prev.map((s, i) => i === idx ? { ...s, title: e.target.value } : s))}
                          placeholder="Titolo sezione"
                          className="text-sm"
                        />
                        <textarea
                          value={section.content}
                          onChange={(e) => setGuideSections((prev) => prev.map((s, i) => i === idx ? { ...s, content: e.target.value } : s))}
                          placeholder="Contenuto…"
                          rows={3}
                          className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm resize-y"
                        />
                      </div>
                    ))}
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`
                        setGuideSections((prev) => [
                          ...prev,
                          { id: newId, type: "text", title: "", content: "", order: prev.length, visible: true },
                        ])
                      }}
                    >
                      <Plus className="h-4 w-4 mr-1" /> Aggiungi sezione
                    </Button>
                  </div>

                  {/* Save + preview */}
                  <div className="flex items-center gap-3 flex-wrap pt-2">
                    <Button
                      disabled={guideSaving}
                      onClick={async () => {
                        setGuideSaving(true)
                        setGuideToast("")
                        const res = await safeFetch(endpoints.admin.events.updateGuide, "PUT", {
                          event_id: eventId,
                          guide: {
                            published: guidePublished,
                            sections: guideSections,
                          },
                        })
                        setGuideSaving(false)
                        setGuideToast(res?.error ? `Errore: ${res.error}` : "Guide salvata.")
                        setTimeout(() => setGuideToast(""), 3000)
                      }}
                    >
                      {guideSaving ? <><Loader2 className="h-4 w-4 mr-2 animate-spin" />Salvataggio…</> : "Salva guide"}
                    </Button>
                    {guidePublished && event?.slug && (
                      <a
                        href={`/events/${event.slug}/guide`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm text-orange-400 hover:underline"
                      >
                        Anteprima →
                      </a>
                    )}
                    {guideToast && (
                      <span className="text-sm text-orange-400">{guideToast}</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </motion.div>

        {/* Modali */}
        <ParticipantModal
          isOpen={isParticipantModalOpen}
          onClose={closeParticipantModal}
          form={participantForm}
          isEditMode={isEditMode}
          membershipOptions={currentYearMemberships}
          currentMembershipYear={currentMembershipYear}
          membershipLoading={membershipsLoading}
          onSubmit={handleParticipantSubmit}
          onInput={(e) =>
            setParticipantForm((f) => ({
              ...f,
              [e.target.name]: e.target.name === "gender"
                ? (e.target.value || "").toLowerCase()
                : e.target.value,
              ...(e.target.name === "membership_id"
                ? {
                    membershipId: e.target.value || null,
                    membership_included: !!e.target.value,
                  }
                : {}),
            }))
          }
          onCheckbox={(name, value) => setParticipantForm((f) => ({ ...f, [name]: value }))}
          onMemberSelect={(member) => {
            if (!member) {
              setParticipantForm((f) => ({
                ...f,
                membership_id: null,
                membershipId: null,
                membership_included: false,
              }))
              return
            }
            setParticipantForm((f) => ({
              ...f,
              name: member.name || f.name,
              surname: member.surname || f.surname,
              email: member.email || f.email,
              phone: member.phone || f.phone,
              birthdate: member.birthdate || f.birthdate,
              membership_id: member.id,
              membershipId: member.id,
              membership_included: false,
            }))
          }}
        />

        <LocationModal
          isOpen={isLocationModalOpen}
          onClose={() => setLocationModalOpen(false)}
          targetName={locationTargetName}
          storedAddress={locationData.address}
          storedMapsUrl={locationData.maps_url}
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
