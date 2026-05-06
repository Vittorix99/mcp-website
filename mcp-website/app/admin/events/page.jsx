"use client"

import { useState, useMemo } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Plus, Edit, Trash2, Eye, Loader2, Users, MoreVertical } from "lucide-react"

import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

import { useAdminEvents } from "@/hooks/useAdminEvents"
import { routes } from "@/config/routes"
import { EventModal } from "@/components/admin/events/EventModal"
import { EVENT_STATUSES, PURCHASE_MODES, resolvePurchaseMode } from "@/config/events-utils"
import { EventThumbnail } from "@/components/admin/events/EventThumbnail"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

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

export default function EventsPage() {
  const router = useRouter()
  const { events, loading, error, createEvent, updateEvent, deleteEvent, refreshEvents } = useAdminEvents()

  const emptyForm = {
    title: "",
    location: "",
    locationHint: "",
    date: "",
    startTime: "",
    endTime: "",
    price: "",
    fee: "",
    note: "",
    lineup: "",
    status: EVENT_STATUSES.ACTIVE,
    purchaseMode: PURCHASE_MODES.PUBLIC,
    image: null,
    allowDuplicates: false,
    onlyFemales: false,
    over21Only: false,
  }

  const [form, setForm] = useState(emptyForm)
  const [originalForm, setOriginalForm] = useState(null)
  const [search, setSearch] = useState("")
  const [isModalOpen, setModalOpen] = useState(false)
  const [isEditMode, setEditMode] = useState(false)
  const [selectedEventId, setSelectedEventId] = useState(null)

  const onInput = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  const onCheckbox = (name, value) => {
    setForm((f) => ({ ...f, [name]: value }))
  }
  const onSelectPurchaseMode = (e) => setForm((f) => ({ ...f, purchaseMode: e.target.value }))
  const onFileChange = (e) => setForm((f) => ({ ...f, image: e.target.files[0] }))

  function openModal(id = null) {
    if (id) {
      const ev = events.find((x) => x.id === id)
      if (!ev) return
      const [d, m, y] = ev.date.split("-")
      const norm = {
        title: ev.title,
        location: ev.location,
        locationHint: ev.locationHint || "",
        date: `${y}-${m}-${d}`,
        startTime: ev.startTime,
        endTime: ev.endTime,
        price: ev.price?.toString() || "",
        fee: ev.fee?.toString() || "",
        note: ev.note || "",
        lineup: (ev.lineup || []).join("\n"),
        status: ev.status || EVENT_STATUSES.ACTIVE,
        allowDuplicates: !!ev.allowDuplicates,
        purchaseMode: resolvePurchaseMode(ev),
        onlyFemales: !!ev.onlyFemales,
        over21Only: !!ev.over21Only,
        image: null,
      }
      setForm(norm)
      setOriginalForm(norm)
      setEditMode(true)
      setSelectedEventId(id)
    } else {
      setForm(emptyForm)
      setOriginalForm(null)
      setEditMode(false)
      setSelectedEventId(null)
    }
    setModalOpen(true)
  }

  function closeModal() {
    setModalOpen(false)
    setForm(emptyForm)
    setOriginalForm(null)
    setEditMode(false)
    setSelectedEventId(null)
  }

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      if (isEditMode) {
        const diff = {}
        for (const key in form) {
          if (form[key] !== originalForm[key]) diff[key] = form[key]
        }
        if (Object.keys(diff).length === 0) {
          closeModal()
          return
        }
        await updateEvent(selectedEventId, diff)
      } else {
        await createEvent(form)
      }
      closeModal()
    } catch (err) {
      console.error("Errore submit:", err)
    }
  }

  async function handleDelete(id) {
    if (confirm("Eliminare evento?")) await deleteEvent(id)
  }

  function formatDate(ds) {
    if (!ds || typeof ds !== "string") return "Data non valida"
    const parts = ds.split("-")
    if (parts.length !== 3) return "Formato non valido"
    const [d, m, y] = parts
    return `${d}/${m}/${y}`
  }

  function getStatus(ev) {
    if (!ev || !ev.date) return { label: "Dati mancanti", color: "bg-[var(--color-red)]" }
    const [d, m, y] = ev.date.split("-").map(Number)
    const now = new Date()
    now.setHours(0, 0, 0, 0)
    const dt = new Date(y, m - 1, d)
    if (isNaN(dt.getTime())) return { label: "Data errata", color: "bg-[var(--color-red)]" }
    const status = ev.status || EVENT_STATUSES.ACTIVE
    if (status === EVENT_STATUSES.COMING_SOON) return { label: "Coming soon", color: "bg-[var(--color-purple)]" }
    if (status === EVENT_STATUSES.SOLD_OUT) return { label: "Sold out", color: "bg-[var(--color-orange)]" }
    if (status === EVENT_STATUSES.ENDED || dt < now) return { label: "Terminato", color: "bg-[var(--color-muted)]" }
    if (status === EVENT_STATUSES.ACTIVE) return { label: "Attivo", color: "bg-emerald-700" }
    return { label: "Sconosciuto", color: "bg-[var(--color-muted)]" }
  }

  const filtered = useMemo(() => {
    return events
      .filter(
        (ev) => {
          const locText = (ev.locationHint || ev.location || "").toLowerCase()
          return ev.title.toLowerCase().includes(search.toLowerCase()) || locText.includes(search.toLowerCase())
        },
      )
      .sort((a, b) => {
        const [da, ma, ya] = a.date.split("-").map(Number)
        const [db, mb, yb] = b.date.split("-").map(Number)
        return new Date(yb, mb - 1, db).getTime() - new Date(ya, ma - 1, da).getTime()
      })
  }, [events, search])

  return (
    <motion.div
      className="space-y-6 pb-8"
      style={ADMIN_THEME}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <AdminPageHeader
        title="Eventi"
        description="Crea, modifica e gestisci eventi MCP."
        backHref={routes.admin.dashboard}
        backLabel="Torna alla dashboard"
        actions={(
          <>
            <Button variant="outline" onClick={refreshEvents} disabled={loading} className="bg-transparent">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Aggiorna"}
            </Button>
            <Button onClick={() => openModal()}>
              <Plus className="h-4 w-4 mr-2" /> Nuovo Evento
            </Button>
          </>
        )}
      />

      {/* STATS */}
      <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
        {[
          { label: "EVENTI TOTALI", value: events.length },
          { label: "EVENTI ATTIVI", value: events.filter((e) => getStatus(e).label === "Attivo").length },
          { label: "EVENTI TERMINATI", value: events.filter((e) => getStatus(e).label === "Terminato").length },
          { label: "PARTECIPANTI TOT.", value: events.reduce((s, e) => s + (e.participantsCount || 0), 0) },
        ].map(({ label, value }) => (
          <Card key={label} className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)]">
            <CardContent className="p-4">
              <p className="text-xs uppercase tracking-[0.08em] text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>{label}</p>
              <p className="mt-2 text-2xl text-[var(--color-white)]" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* TABLE CONTAINER */}
      <Card className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)]">
        <CardHeader className="flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-[var(--color-border)] pb-4">
          <div>
            <CardTitle className="uppercase tracking-wide text-[var(--color-white)]" style={{ fontFamily: TITLE_FONT, fontWeight: 800 }}>Eventi</CardTitle>
            <CardDescription className="text-[var(--color-off)]">{filtered.length} trovati</CardDescription>
          </div>
          <Input
            placeholder="Cerca evento..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full md:max-w-sm rounded-none border-[var(--color-border)] bg-[var(--color-black)] text-[var(--color-white)] placeholder:text-[var(--color-off)] focus-visible:ring-[var(--color-orange)]"
          />
        </CardHeader>
        <CardContent>
          {/* DESKTOP TABLE */}
          <div className="hidden md:block overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Evento</TableHead>
                  <TableHead>Data/Ora</TableHead>
                  <TableHead>Partecipanti</TableHead>
                  <TableHead>Stato</TableHead>
                  <TableHead className="text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading && !events.length ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-8 text-center">
                      <Loader2 className="mx-auto h-8 w-8 animate-spin text-mcp-orange" />
                    </TableCell>
                  </TableRow>
                ) : filtered.length ? (
                  filtered.map((ev) => {
                    const st = getStatus(ev)
                    const purchaseMode = resolvePurchaseMode(ev)
                    return (
                      <TableRow key={ev.id} className="border-[var(--color-border)] hover:bg-[var(--color-surface)]">
                        <TableCell>
                          <div className="flex items-center gap-4">
                            {ev.image && <EventThumbnail imageName={ev.image} alt={ev.title} />}
                            <div>
                              <div className="font-bold text-[var(--color-white)]" style={{ fontFamily: TITLE_FONT }}>{ev.title}</div>
                              <div className="text-sm text-[var(--color-off)]">{ev.location}</div>
                              <div className="text-xs text-[var(--color-muted)] italic">{purchaseMode}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="font-medium text-[var(--color-white)]">{formatDate(ev.date)}</div>
                          <div className="text-sm text-[var(--color-off)]">{ev.startTime}</div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2 text-[var(--color-white)]">
                            <Users className="h-4 w-4 text-[var(--color-off)]" />
                            {ev.participantsCount || 0}
                            {ev.maxParticipants ? <span className="text-[var(--color-off)]">/{ev.maxParticipants}</span> : ""}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={`${st.color} text-white p-2 whitespace-nowrap rounded-none`}>{st.label}</Badge>
                        </TableCell>
                        <TableCell className="text-right space-x-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => router.push(routes.admin.eventDetails(ev.id))}                          >
                            <Eye className="h-5 w-5" />
                          </Button>
                          <Button variant="ghost" size="icon" onClick={() => openModal(ev.id)}>
                            <Edit className="h-5 w-5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="text-red-400 hover:text-red-500"
                            onClick={() => handleDelete(ev.id)}
                          >
                            <Trash2 className="h-5 w-5" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} className="p-8 text-center text-gray-400">
                      Nessun evento trovato.
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>

          {/* MOBILE CARDS */}
          <div className="block md:hidden space-y-4">
            {loading && !events.length ? (
              <div className="p-8 text-center">
                <Loader2 className="mx-auto h-8 w-8 animate-spin text-mcp-orange" />
              </div>
            ) : filtered.length ? (
              filtered.map((ev) => {
                const st = getStatus(ev)
                const purchaseMode = resolvePurchaseMode(ev)
                return (
                  <Card key={ev.id} className="rounded-none border-[var(--color-border)] bg-[var(--color-surface)]">
                    <CardHeader className="flex flex-row items-start justify-between gap-4 p-4 border-b border-[var(--color-border)]">
                      <div className="flex items-start gap-4">
                        {ev.image && <EventThumbnail imageName={ev.image} alt={ev.title} className="w-16 h-16" />}
                        <div>
                          <h3 className="font-bold text-[var(--color-white)]" style={{ fontFamily: TITLE_FONT }}>{ev.title}</h3>
                          <p className="text-sm text-[var(--color-off)]">{ev.location}</p>
                          <p className="text-xs italic text-[var(--color-muted)]">{purchaseMode}</p>
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-5 w-5" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => router.push(routes.admin.eventDetails(ev.id))}>
                            <Eye className="mr-2 h-4 w-4" /> Vedi
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openModal(ev.id)}>
                            <Edit className="mr-2 h-4 w-4" /> Modifica
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleDelete(ev.id)} className="text-red-500 focus:text-red-500">
                            <Trash2 className="mr-2 h-4 w-4" /> Elimina
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </CardHeader>
                    <CardContent className="p-4 pt-0 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-xs uppercase tracking-wide text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>Data/Ora</p>
                        <p className="mt-1 text-[var(--color-white)]">{formatDate(ev.date)}</p>
                        <p className="text-[var(--color-off)]">{ev.startTime}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-wide text-[var(--color-off)]" style={{ fontFamily: TITLE_FONT, fontWeight: 700 }}>Partecipanti</p>
                        <div className="mt-1 flex items-center gap-2 text-[var(--color-white)]">
                          <Users className="h-4 w-4 text-[var(--color-off)]" />
                          {ev.participantsCount || 0}
                          {ev.maxParticipants ? <span className="text-[var(--color-off)]">/{ev.maxParticipants}</span> : ""}
                        </div>
                      </div>
                    </CardContent>
                    <CardFooter className="p-4 pt-0">
                      <Badge className={`${st.color} text-white p-2 w-full justify-center rounded-none`}>{st.label}</Badge>
                    </CardFooter>
                  </Card>
                )
              })
            ) : (
              <div className="p-8 text-center text-gray-400">Nessun evento trovato.</div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* MODAL */}
      <EventModal
        isOpen={isModalOpen}
        form={form}
        loading={loading}
        isEditMode={isEditMode}
        onClose={closeModal}
        onSubmit={handleSubmit}
        onInput={onInput}
        onCheckbox={onCheckbox}
        onSelectMode={onSelectPurchaseMode}
        onFileChange={onFileChange}
      />
    </motion.div>
  )
}
