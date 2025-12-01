"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { ArrowLeft, Plus, Loader2, Download, Eye, Ticket, Trash2, Edit, MoreVertical } from "lucide-react"
import { motion } from "framer-motion"
import * as XLSX from "xlsx"
import {routes} from "@/config/routes"

import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"

import MembershipStats from "@/components/admin/memberships/MembershipStats"
import { downloadStorageFile } from "@/config/firebaseStorage"
import { useAdminMemberships } from "@/hooks/useAdminMemberships"
import { MembershipModal } from "@/components/admin/memberships/MembershipsModal"

export default function MembershipsPage() {
  const router = useRouter()
  const {
    memberships,
    loadAll,
    create,
    update,
    remove,
    sendCard,
    getCurrentYearPrice,
    setCurrentYearPrice,
    membershipPrice,
    loading,
  } = useAdminMemberships()

  const [search, setSearch] = useState("")
  const [showOnlyNotSent, setShowOnlyNotSent] = useState(false)
  const [phoneFilter, setPhoneFilter] = useState("")
  const [emailFilter, setEmailFilter] = useState("")
  const [modalOpen, setModalOpen] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const [form, setForm] = useState({})
  const [initial, setInitial] = useState({})
  const [priceEditing, setPriceEditing] = useState(false)
  const [tempPrice, setTempPrice] = useState("")

  const currentYear = new Date().getFullYear().toString()

  useEffect(() => {
    loadAll()
    getCurrentYearPrice()
  }, [loadAll, getCurrentYearPrice])

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

  const filtered = useMemo(() => {
    const s = (search || "").toLowerCase()
    const e = (emailFilter || "").toLowerCase()
    const p = (phoneFilter || "").trim()

    return memberships.filter((m) => {
      const fullName = `${m.name || ""} ${m.surname || ""}`.toLowerCase()
      const phoneVal = (m.phone || "")
      const emailVal = (m.email || "").toLowerCase()

      if (s && !fullName.includes(s)) return false
      if (showOnlyNotSent && !!m.membership_sent) return false
      if (p && !phoneVal.includes(p)) return false
      if (e && !emailVal.includes(e)) return false
      return true
    })
  }, [memberships, search, showOnlyNotSent, phoneFilter, emailFilter])

  const stats = useMemo(
    () => ({
      total: memberships.length,
      valid: memberships.filter((m) => m.subscription_valid).length,
    }),
    [memberships],
  )

  const totalTesseramenti = useMemo(() => {
    if (!membershipPrice || membershipPrice.year !== currentYear) return 0
    const count = memberships.filter((m) => new Date(m.start_date).getFullYear().toString() === currentYear).length
    return count * membershipPrice.price
  }, [memberships, membershipPrice, currentYear])

  const onSavePrice = async () => {
    const val = Number.parseFloat(tempPrice)
    if (!isNaN(val)) {
      await setCurrentYearPrice(val)
      setPriceEditing(false)
    }
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

        <Card className="bg-zinc-900 border border-zinc-700">
          <CardHeader>
            <CardTitle>Prezzo Membership ({currentYear})</CardTitle>
          </CardHeader>
          <CardContent className="flex items-center gap-4">
            {priceEditing ? (
              <>
                <Input
                  type="number"
                  value={tempPrice}
                  onChange={(e) => setTempPrice(e.target.value)}
                  placeholder="€"
                  className="w-24"
                />
                <Button size="sm" onClick={onSavePrice}>
                  Salva
                </Button>
                <Button size="sm" variant="outline" onClick={() => setPriceEditing(false)}>
                  Annulla
                </Button>
              </>
            ) : (
              <>
                <span className="text-xl font-semibold">
                  {membershipPrice && membershipPrice.year === currentYear
                    ? `${membershipPrice.price} €`
                    : "Non definito"}
                </span>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => {
                    setTempPrice(membershipPrice?.price?.toString() || "")
                    setPriceEditing(true)
                  }}
                >
                  <Edit className="h-5 w-5" />
                </Button>
              </>
            )}
          </CardContent>
        </Card>

        <MembershipStats stats={stats} totalTesseramenti={totalTesseramenti} onRefresh={loadAll} />

        <div className="flex flex-col md:flex-row gap-2">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cerca membro..."
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
          <Input
            value={phoneFilter}
            onChange={(e) => setPhoneFilter(e.target.value)}
            placeholder="Filtra per telefono"
            className="md:max-w-xs"
          />
          <Input
            value={emailFilter}
            onChange={(e) => setEmailFilter(e.target.value)}
            placeholder="Filtra per email"
            className="md:max-w-xs"
          />
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
                        <TableHead>Validità</TableHead>
                        <TableHead>Tessera</TableHead>
                        <TableHead className="text-right">Azioni</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filtered.map((m) => (
                        <TableRow key={m.id}>
                          <TableCell>
                            <div className="font-medium">
                              {m.name} {m.surname}
                            </div>
                            <div className="text-sm text-gray-400">{m.phone || "N/D"}</div>
                          </TableCell>
                          <TableCell>{m.email}</TableCell>
                          <TableCell>
                            {!m.subscription_valid || isExpired(m.end_date) ? (
                              <Badge variant="destructive">Scaduta</Badge>
                            ) : (
                              <Badge variant="success">{m.end_date}</Badge>
                            )}
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
                  {filtered.map((m) => (
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
                            {m.card_url && (
                              <DropdownMenuItem onClick={() => downloadStorageFile(m.card_url)}>
                                <Download className="mr-2 h-4 w-4" /> Scarica Tessera
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
            {filtered.length === 0 && !loading && (
              <div className="text-center py-12 text-gray-500">Nessun membro trovato.</div>
            )}
          </CardContent>
        </Card>

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
