"use client"

// Force SSR in Next.js (important for Firebase Hosting)

// Force SSR in Next.js (important for Firebase Hosting)

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
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
} from "lucide-react"
import { motion } from "framer-motion"

import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Badge } from "@/components/ui/badge"

import { useAdminEvents } from "@/hooks/useAdminEvents"
import { useAdminParticipants } from "@/hooks/useAdminParticipants"
import { getImageUrl, downloadStorageFile } from "@/config/firebaseStorage"
import { ParticipantModal } from "@/components/admin/participants/ParticipantModal"
import { LocationModal } from "@/components/admin/events/LocationModal"
import { EventStats } from "@/components/admin/events/EventStats"
import { exportParticipantsToExcel } from "@/lib/excel" // ✅ NUOVO IMPORT

export default function EventContent({ id: eventId }) {
  const router = useRouter()
  const { events, loading: evLoad } = useAdminEvents()
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
  } = useAdminParticipants(eventId)

  const [event, setEvent] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [search, setSearch] = useState("")

  const [isParticipantModalOpen, setParticipantModalOpen] = useState(false)
  const [participantForm, setParticipantForm] = useState({})
  const [initialForm, setInitialForm] = useState(null)
  const [isEditMode, setEditMode] = useState(false)

  const [isLocationModalOpen, setLocationModalOpen] = useState(false)
  const [locationTargetName, setLocationTargetName] = useState("")
  const [selectedParticipantId, setSelectedParticipantId] = useState(null)
  const [address, setAddress] = useState("")
  const [link, setLink] = useState("")

  useEffect(() => {
    loadAll()
  }, [eventId, loadAll])

  useEffect(() => {
    const e = events.find((e) => e.id === eventId)
    if (e) {
      setEvent(e)
      if (e.image) {
        getImageUrl("events", `${e.image}.jpg`).then(setImageUrl).catch(console.error)
      }
    }
  }, [events, eventId])

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

  const filtered = useMemo(
    () => participants.filter((p) => `${p.name} ${p.surname}`.toLowerCase().includes(search.toLowerCase())),
    [participants, search],
  )

  const sorted = useMemo(() => [...filtered].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)), [filtered])

  const stats = useMemo(
    () => ({
      total: participants.length,
      new24h: participants.filter((p) => new Date(p.createdAt) >= Date.now() - 86400000).length,
    }),
    [participants],
  )

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
    setLocationModalOpen(true)
    setLocationTargetName(null)
  }

  const openLocationModalForOne = (p) => {
    setLocationModalOpen(true)
    setLocationTargetName(`${p.name} ${p.surname}`)
    setSelectedParticipantId(p.id)
  }

  const handleSendLocation = async ({ address, link }) => {
    if (locationTargetName) {
      await sendLocation(selectedParticipantId, { address, link })
    } else {
      await sendLocationToAll({ address, link })
    }
    setLocationModalOpen(false)
  }

  if (evLoad || !event) {
    return (
      <div className="flex items-center justify-center h-screen  text-white">
        <Loader2 className="animate-spin h-8 w-8" />
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className=" text-gray-50 min-h-screen p-6 lg:p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-7xl mx-auto space-y-6"
        >
          <Button variant="ghost" onClick={() => router.push("/admin/events")}>
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
    <CardContent className="space-y-5 text-base leading-relaxed ">
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
        <strong>Tipo:</strong> {event.type ?? "N/A"}
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
        <p className="text-2xl font-bold mb-3 flex justify-center items-center gap-2 ">
          <Users size={22} />
          Lineup
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
          <StickyNote size={20} />
          <strong>Note:</strong>
        </p>
        <p className="mt-2 text-sm">{event.note || "-"}</p>
      </div>
    </CardContent>
  </Card>
</div>

          
          
          
          {/* Statistiche partecipanti */}
          
          <EventStats participants={participants} onRefresh={loadAll} />

          {/* Participants */}
          <Card>
            <CardHeader className="flex flex-wrap justify-between items-center gap-4">
              <div>
                <CardTitle>Partecipanti ({stats.total})</CardTitle>
                <CardDescription>Lista & azioni</CardDescription>
              </div>
              <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
                <input
                  className="px-3 py-2 bg-gray-800 border border-gray-700 rounded flex-1 sm:w-64"
                  placeholder="Cerca partecipante..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <Button onClick={() => openParticipantModal()}>
                  <Plus className="mr-2" />
                  Aggiungi
                </Button>
                <Button onClick={() => openLocationModalForAll("tutti")}>
                  <Send className="mr-2" />
                  Invia Location a tutti
                </Button>
                <Button onClick={exportToExcel} disabled={!sorted.length}>
                  <Download className="mr-2" />
                  Esporta
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {pLoad ? (
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
                      {sorted.map((p) => (
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
                                onClick={() => router.push(`/admin/memberships/${p.membershipId}`)}
                              >
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
                                onClick={() => router.push(`/admin/purchases?purchaseId=${p.purchase_id}`)}
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
                      {sorted.length === 0 && (
                        <TableRow>
                          <TableCell colSpan={visibleCols.length + 2} className="text-center py-12">
                            Nessun partecipante.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
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
          onSubmit={handleSendLocation}
        />
      </div>
    </TooltipProvider>
  )
}
