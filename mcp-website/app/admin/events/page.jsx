"use client"

import { useState, useMemo } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Plus, Edit, Trash2, Eye, Loader2, Users, MoreVertical, ArrowLeft } from "lucide-react"

import { Card, CardHeader, CardContent, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

import { useAdminEvents } from "@/hooks/useAdminEvents"
import { routes } from "@/config/routes"
import { EventModal } from "@/components/admin/events/EventModal"
import { EVENT_TYPES } from "@/config/events-utils"
import { EventThumbnail } from "@/components/admin/events/EventThumbnail"

export default function EventsPage() {
  const router = useRouter()
  const { events, loading, error, createEvent, updateEvent, deleteEvent, refreshEvents } = useAdminEvents()

  const emptyForm = {
    title: "",
    location: "",
    date: "",
    startTime: "",
    endTime: "",
    price: "",
    fee:"",
    membershipFee: "",
    note: "",
    lineup: "",
    active: true,
    type: EVENT_TYPES.STANDARD,
    image: null,
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
  const onSelectType = (e) => setForm((f) => ({ ...f, type: e.target.value }))
  const onFileChange = (e) => setForm((f) => ({ ...f, image: e.target.files[0] }))

  function openModal(id = null) {
    if (id) {
      const ev = events.find((x) => x.id === id)
      if (!ev) return
      const [d, m, y] = ev.date.split("-")
      const norm = {
        title: ev.title,
        location: ev.location,
        date: `${y}-${m}-${d}`,
        startTime: ev.startTime,
        endTime: ev.endTime,
        price: ev.price?.toString() || "",
        fee: ev.fee?.toString() || "",
        membershipFee: ev.membershipFee?.toString() || "",
        note: ev.note || "",
        lineup: (ev.lineup || []).join("\n"),
        active: !!ev.active,
        type: ev.type || EVENT_TYPES.STANDARD,
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
    if (!ev || !ev.date) return { label: "Dati mancanti", color: "bg-red-500" }
    const [d, m, y] = ev.date.split("-").map(Number)
    const now = new Date()
    now.setHours(0, 0, 0, 0)
    const dt = new Date(y, m - 1, d)
    if (isNaN(dt.getTime())) return { label: "Data errata", color: "bg-red-500" }
    if (!ev.active) return { label: "Non Attivo", color: "bg-neutral-500" }
    if (dt < now) return { label: "Terminato", color: "bg-gray-500" }
    return { label: "Attivo", color: "bg-green-600" }
  }

  const filtered = useMemo(() => {
    return events
      .filter(
        (ev) =>
          ev.title.toLowerCase().includes(search.toLowerCase()) ||
          ev.location.toLowerCase().includes(search.toLowerCase()),
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
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* HEADER */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
                <Button variant="ghost" onClick={() => router.push("/admin")}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Torna admin
          </Button>
          
          <h1 className="text-3xl md:text-4xl font-bold gradient-text mt-2">Gestione Eventi</h1>
          <p className="text-gray-300">Crea, modifica e gestisci eventi MCP.</p>
        </div>
        <div className="flex gap-2 w-full md:w-auto">
          <Button
            variant="outline"
            onClick={refreshEvents}
            disabled={loading}
            className="flex-1 md:flex-none bg-transparent"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Aggiorna"}
          </Button>
          <Button onClick={() => openModal()} className="flex-1 md:flex-none">
            <Plus className="h-4 w-4 mr-2" /> Nuovo Evento
          </Button>
        </div>
      </div>

      {/* STATS */}
      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle>Eventi Totali</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{events.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Eventi Attivi</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{events.filter((e) => getStatus(e).label === "Attivo").length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Eventi Terminati</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{events.filter((e) => getStatus(e).label === "Terminato").length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Partecipanti</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{events.reduce((s, e) => s + (e.participantsCount || 0), 0)}</div>
          </CardContent>
        </Card>
      </div>

      {/* TABLE CONTAINER */}
      <Card>
        <CardHeader className="flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <CardTitle>Eventi</CardTitle>
            <CardDescription>{filtered.length} trovati</CardDescription>
          </div>
          <Input
            placeholder="Cerca evento..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full md:max-w-sm"
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
                    return (
                      <TableRow key={ev.id}>
                        <TableCell>
                          <div className="flex items-center gap-4">
                            {ev.image && <EventThumbnail imageName={ev.image} alt={ev.title} />}
                            <div>
                              <div className="font-medium">{ev.title}</div>
                              <div className="text-sm text-gray-400">{ev.location}</div>
                              <div className="text-xs text-gray-500 italic">{ev.type}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <div>{formatDate(ev.date)}</div>
                          <div className="text-sm text-gray-400">{ev.startTime}</div>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Users className="h-4 w-4" />
                            {ev.participantsCount || 0}
                            {ev.maxParticipants ? `/${ev.maxParticipants}` : ""}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge className={`${st.color} text-white p-2 whitespace-nowrap`}>{st.label}</Badge>
                        </TableCell>
                        <TableCell className="text-right space-x-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => router.push(routes.admin.events + `/${ev.id}`)}
                          >
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
                return (
                  <Card key={ev.id} className="bg-neutral-900 border-neutral-800">
                    <CardHeader className="flex flex-row items-start justify-between gap-4 p-4">
                      <div className="flex items-start gap-4">
                        {ev.image && <EventThumbnail imageName={ev.image} alt={ev.title} className="w-16 h-16" />}
                        <div>
                          <h3 className="font-bold">{ev.title}</h3>
                          <p className="text-sm text-gray-400">{ev.location}</p>
                          <p className="text-xs text-gray-500 italic">{ev.type}</p>
                        </div>
                      </div>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-5 w-5" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => router.push(routes.admin.events + `/${ev.id}`)}>
                            <Eye className="mr-2 h-4 w-4" /> Vedi
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openModal(ev.id)}>
                            <Edit className="mr-2 h-4 w-4" /> Modifica
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDelete(ev.id)}
                            className="text-red-500 focus:text-red-500"
                          >
                            <Trash2 className="mr-2 h-4 w-4" /> Elimina
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </CardHeader>
                    <CardContent className="p-4 pt-0 grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="font-semibold">Data/Ora</p>
                        <p>{formatDate(ev.date)}</p>
                        <p className="text-gray-400">{ev.startTime}</p>
                      </div>
                      <div>
                        <p className="font-semibold">Partecipanti</p>
                        <div className="flex items-center gap-2">
                          <Users className="h-4 w-4" />
                          {ev.participantsCount || 0}
                          {ev.maxParticipants ? `/${ev.maxParticipants}` : ""}
                        </div>
                      </div>
                    </CardContent>
                    <CardFooter className="p-4 pt-0">
                      <Badge className={`${st.color} text-white p-2 w-full justify-center`}>{st.label}</Badge>
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
        onSelectType={onSelectType}
        onFileChange={onFileChange}
      />
    </motion.div>
  )
}
