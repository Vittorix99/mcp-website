"use client"

// Force SSR in Next.js (important for Firebase Hosting)

// Force SSR in Next.js (important for Firebase Hosting)

import { useState, useEffect, useMemo, useRef } from "react"
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
  X
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

import { useAdminEvents } from "@/hooks/useAdminEvents"
import { useAdminParticipants } from "@/hooks/useAdminParticipants"
import { getImageUrl, downloadStorageFile } from "@/config/firebaseStorage"
import { ParticipantModal } from "@/components/admin/participants/ParticipantModal"
import { LocationModal } from "@/components/admin/events/LocationModal"
import { EventStats } from "@/components/admin/events/EventStats"
import { exportParticipantsToExcel } from "@/lib/excel" // ✅ NUOVO IMPORT
import { resolvePurchaseMode } from "@/config/events-utils"

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

  useEffect(() => {
    loadAll()
  }, [eventId, loadAll])

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

  // ✅ Nuova versione export
  const exportToExcel = () => {
    exportParticipantsToExcel(sorted, event?.title, eventId)
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
                  <Info size={20} />
                  <strong>Purchase mode:</strong> {purchaseMode}
                </p>
                <p className="flex items-center gap-3">
                  <IdCard size={20} />
                  <strong>Tessera:</strong> {event.membershipFee ?? "N/A"} €
                </p>

                <div className="flex items-center gap-3">
                  <Users size={20} />
                  <strong>Stato:</strong>
                  <Badge variant={event.active ? "success" : "secondary"} className="text-sm px-2 py-0.5">
                    {event.active ? "Attivo" : "Non attivo"}
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

          {(!event.active || isPastEvent) && (
            <div className="rounded-xl border border-zinc-700 bg-zinc-900/70 p-4 text-center">
              <p className="text-lg font-semibold text-white">
                {isPastEvent ? "Evento terminato" : "Evento in arrivo"}
              </p>
              <p className="text-sm text-gray-400">
                {isPastEvent
                  ? "Questo evento è già stato completato. Puoi comunque gestire i partecipanti e le statistiche."
                  : "L’evento non è ancora attivo. Aggiorna lo stato quando sarà pronto per la vendita."}
              </p>
            </div>
          )}

          {/* Statistiche partecipanti */}
          <EventStats participants={participants} onRefresh={loadAll} />

          {/* Participants */}
          <Card>
            <CardHeader className="flex flex-wrap justify-between items-center gap-4">
              <div>
                <CardTitle>Partecipanti ({filteredCount} / {stats.total})</CardTitle>
                <CardDescription>Lista & azioni</CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                <input
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded flex-1 sm:w-64"
                  placeholder="Cerca partecipante..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <select
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded"
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
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded"
                  value={locationFilter}
                  onChange={(e) => setLocationFilter(e.target.value)}
                  aria-label="Filtra per location inviata"
                >
                  <option value="all">Location: tutte</option>
                  <option value="yes">Inviata</option>
                  <option value="no">Non inviata</option>
                </select>

                <select
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded"
                  value={memberFilter}
                  onChange={(e) => setMemberFilter(e.target.value)}
                  aria-label="Filtra per membro"
                >
                  <option value="all">Membro: tutti</option>
                  <option value="yes">Sì</option>
                  <option value="no">No</option>
                </select>
                <Button onClick={() => openParticipantModal()}>
                  <Plus className="mr-2" /> Aggiungi
                </Button>
                <Button onClick={() => openLocationModalForAll("tutti")}>
                  <Send className="mr-2" /> Invia Location a tutti
                </Button>
                <Button onClick={exportToExcel} disabled={!sorted.length}>
                  <Download className="mr-2" /> Esporta
                </Button>
                <Button variant="secondary"   onClick={() => router.push(routes.admin.checkin(eventId))}
>
                  In the event
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
                          <TableHead className="text-center">Ingresso</TableHead>
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
                                  const qs = new URLSearchParams({ purchaseId: String(p.purchase_id || "") });
                                  console.debug("[navigate]", routes.admin.purchases + "?" + qs.toString());
                                  router.push(`${routes.admin.purchases}?${qs.toString()}`);
                                }}
                              >
                                Vai
                              </Button>
                              ) : (
                                "-"
                              )}
                            </TableCell>
                            {/* Ingresso (check-in) column */}
                            <TableCell className="text-center">
                              {p.entered ? (
                                <div className="flex items-center justify-center gap-2">
                                  <Badge variant="success">Entrato</Badge>
                                  <Button variant="outline" size="sm" onClick={() => update(p.id, { entered: false })}>Annulla</Button>
                                </div>
                              ) : (
                                <div className="flex items-center justify-center gap-2">
                                  <Badge variant="secondary">No</Badge>
                                  <Button size="sm" onClick={() => update(p.id, { entered: true, entered_at: new Date().toISOString() })}>Entra</Button>
                                </div>
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
