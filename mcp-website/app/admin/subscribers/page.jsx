"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
  ArrowLeft,
  Loader2,
  MoreVertical,
  Plus,
  RefreshCw,
  Trash2,
  UserMinus,
  UserPlus,
  Pencil,
} from "lucide-react"

import { routes } from "@/config/routes"
import { useError } from "@/contexts/errorContext"
import {
  assignSubscriberToGroup,
  createMailerLiteField,
  createMailerLiteGroup,
  createMailerLiteSubscriber,
  deleteMailerLiteSubscriber,
  deleteMailerLiteField,
  deleteMailerLiteGroup,
  deleteMailerLiteSegment,
  listMailerLiteFields,
  listMailerLiteGroupSubscribers,
  listMailerLiteGroups,
  listMailerLiteSegments,
  listMailerLiteSubscribers,
  unassignSubscriberFromGroup,
  updateMailerLiteField,
  updateMailerLiteGroup,
  updateMailerLiteSegment,
  updateMailerLiteSubscriber,
} from "@/services/admin/mailerLite"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const STATUS_OPTIONS = ["active", "unsubscribed", "unconfirmed", "junk"]
const FIELD_TYPES = [
  "text",
  "number",
  "date",
  "boolean",
  "select",
  "multi_select",
]

const emptyForm = {
  email: "",
  firstName: "",
  lastName: "",
  company: "",
  city: "",
  country: "",
  phone: "",
  state: "",
  zip: "",
  gender: "",
  birthdate: "",
  status: "active",
  groupId: "none",
}

export default function SubscribersPage() {
  const router = useRouter()
  const { setError } = useError()
  const [loading, setLoading] = useState(false)
  const [groupsLoading, setGroupsLoading] = useState(false)
  const [subscribers, setSubscribers] = useState([])
  const [groups, setGroups] = useState([])
  const [fields, setFields] = useState([])
  const [segments, setSegments] = useState([])
  const [limit] = useState(25)
  const [cursor, setCursor] = useState("")
  const [meta, setMeta] = useState(null)
  const [groupPage, setGroupPage] = useState(1)
  const [groupHasNext, setGroupHasNext] = useState(true)
  const [filters, setFilters] = useState({
    search: "",
    status: "all",
    groupId: "all",
  })
  const [form, setForm] = useState(emptyForm)
  const [isDialogOpen, setDialogOpen] = useState(false)
  const [isEditMode, setEditMode] = useState(false)
  const [selectedSubscriber, setSelectedSubscriber] = useState(null)
  const [groupDialog, setGroupDialog] = useState({
    open: false,
    mode: "assign",
    subscriber: null,
    groupId: "none",
  })
  const [groupModal, setGroupModal] = useState({
    open: false,
    mode: "create",
    group: null,
    name: "",
  })
  const [fieldModal, setFieldModal] = useState({
    open: false,
    mode: "create",
    field: null,
    name: "",
    type: "text",
  })
  const [segmentModal, setSegmentModal] = useState({
    open: false,
    segment: null,
    name: "",
  })

  const blurActiveElement = () => {
    if (typeof document === "undefined") return
    const active = document.activeElement
    if (active && typeof active.blur === "function") {
      active.blur()
    }
  }

  const filteredSubscribers = useMemo(() => {
    return subscribers.filter((subscriber) => {
      const fields = subscriber.fields || {}
      const groupIds = Array.isArray(subscriber.groups)
        ? subscriber.groups
        : Array.isArray(subscriber.group_ids)
          ? subscriber.group_ids
          : null
      const groupCount =
        groupIds !== null
          ? groupIds.length
          : typeof subscriber.groups_count === "number"
            ? subscriber.groups_count
            : null
      const hasGroup = groupCount !== null ? groupCount > 0 : null
      const haystack = [
        subscriber.email,
        fields.name,
        fields.last_name,
        fields.company,
        fields.city,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      const matchesSearch = !filters.search || haystack.includes(filters.search.toLowerCase())
      const matchesStatus = filters.status === "all" || subscriber.status === filters.status
      const matchesGroup =
        filters.groupId === "all"
          ? true
          : filters.groupId === "none"
            ? hasGroup === false
            : true
      return matchesSearch && matchesStatus && matchesGroup
    })
  }, [subscribers, filters.search, filters.status, filters.groupId])

  useEffect(() => {
    fetchGroups()
    fetchFields()
    fetchSegments()
  }, [])

  useEffect(() => {
    fetchSubscribers()
  }, [cursor, limit, filters.groupId, groupPage])

  const fetchGroups = async () => {
    setGroupsLoading(true)
    const response = await listMailerLiteGroups({ limit: 100 })
    if (response?.error) {
      setError(response.error)
    } else {
      setGroups(response?.data || [])
    }
    setGroupsLoading(false)
  }

  const fetchFields = async () => {
    const response = await listMailerLiteFields({ limit: 100 })
    if (response?.error) {
      setError(response.error)
    } else {
      setFields(response?.data || [])
    }
  }

  const fetchSegments = async () => {
    const response = await listMailerLiteSegments({ limit: 100 })
    if (response?.error) {
      setError(response.error)
    } else {
      setSegments(response?.data || [])
    }
  }

  const fetchSubscribers = async () => {
    setLoading(true)
    const response =
      filters.groupId !== "all" && filters.groupId !== "none"
        ? await listMailerLiteGroupSubscribers(filters.groupId, { limit, page: groupPage })
        : await listMailerLiteSubscribers({ limit, cursor })
    if (response?.error) {
      setError(response.error)
    } else {
      setSubscribers(response?.data || [])
      if (filters.groupId !== "all" && filters.groupId !== "none") {
        setMeta(null)
        setGroupHasNext((response?.data || []).length === limit)
      } else {
        setMeta(response?.meta || null)
      }
    }
    setLoading(false)
  }

  const openCreateDialog = () => {
    setForm(emptyForm)
    setEditMode(false)
    setSelectedSubscriber(null)
    setDialogOpen(true)
  }

  const openEditDialog = (subscriber) => {
    const fields = subscriber.fields || {}
    setForm({
      email: subscriber.email || "",
      firstName: fields.name || "",
      lastName: fields.last_name || "",
      company: fields.company || "",
      city: fields.city || "",
      country: fields.country || "",
      phone: fields.phone || "",
      state: fields.state || "",
      zip: fields.z_i_p || "",
      gender: fields.gender || "",
      birthdate: normalizeDateInput(fields.birthdate),
      status: subscriber.status || "active",
      groupId: "none",
    })
    setEditMode(true)
    setSelectedSubscriber(subscriber)
    setDialogOpen(true)
  }

  const closeDialog = () => {
    setDialogOpen(false)
    setForm(emptyForm)
    setEditMode(false)
    setSelectedSubscriber(null)
  }

  const handleFormChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const submitSubscriber = async (event) => {
    event.preventDefault()
    if (!form.email) {
      setError("Inserisci un'email valida.")
      return
    }

    const payload = {
      email: form.email,
      status: form.status,
      fields: {
        name: form.firstName || null,
        last_name: form.lastName || null,
        company: form.company || null,
        city: form.city || null,
        country: form.country || null,
        phone: form.phone || null,
        state: form.state || null,
        z_i_p: form.zip || null,
        gender: form.gender || null,
        birthdate: form.birthdate || null,
      },
    }

    let response
    if (isEditMode) {
      response = await updateMailerLiteSubscriber(payload)
    } else {
      const groupId = form.groupId !== "none" ? Number(form.groupId) : null
      response = await createMailerLiteSubscriber({
        ...payload,
        groups: groupId ? [groupId] : undefined,
      })
    }

    if (response?.error) {
      setError(response.error)
      return
    }
    closeDialog()
    fetchSubscribers()
  }

  const handleDelete = async (subscriber) => {
    if (!confirm(`Eliminare ${subscriber.email}?`)) return
    const response = await deleteMailerLiteSubscriber(subscriber.id)
    if (response?.error) {
      setError(response.error)
      return
    }
    fetchSubscribers()
  }

  const openGroupDialog = (subscriber, mode) => {
    setGroupDialog({ open: true, mode, subscriber, groupId: "none" })
  }

  const closeGroupDialog = () => {
    setGroupDialog({ open: false, mode: "assign", subscriber: null, groupId: "none" })
  }

  const submitGroupDialog = async () => {
    if (!groupDialog.subscriber || groupDialog.groupId === "none") {
      setError("Seleziona un gruppo valido.")
      return
    }
    const action =
      groupDialog.mode === "assign" ? assignSubscriberToGroup : unassignSubscriberFromGroup
    const response = await action(groupDialog.subscriber.id, groupDialog.groupId)
    if (response?.error) {
      setError(response.error)
      return
    }
    closeGroupDialog()
    fetchSubscribers()
  }

  const openGroupModal = (mode, group = null) => {
    setGroupModal({
      open: true,
      mode,
      group,
      name: group?.name || "",
    })
  }

  const closeGroupModal = () => {
    setGroupModal({ open: false, mode: "create", group: null, name: "" })
  }

  const submitGroupModal = async () => {
    if (!groupModal.name.trim()) {
      setError("Inserisci un nome gruppo valido.")
      return
    }
    const response =
      groupModal.mode === "create"
        ? await createMailerLiteGroup(groupModal.name.trim())
        : await updateMailerLiteGroup(groupModal.group?.id, groupModal.name.trim())
    if (response?.error) {
      setError(response.error)
      return
    }
    closeGroupModal()
    fetchGroups()
  }

  const handleDeleteGroup = async (group) => {
    if (!confirm(`Eliminare il gruppo "${group.name}"?`)) return
    const response = await deleteMailerLiteGroup(group.id)
    if (response?.error) {
      setError(response.error)
      return
    }
    fetchGroups()
  }

  const openFieldModal = (mode, field = null) => {
    setFieldModal({
      open: true,
      mode,
      field,
      name: field?.name || "",
      type: field?.type || "text",
    })
  }

  const closeFieldModal = () => {
    setFieldModal({ open: false, mode: "create", field: null, name: "", type: "text" })
  }

  const submitFieldModal = async () => {
    if (!fieldModal.name.trim()) {
      setError("Inserisci un nome campo valido.")
      return
    }
    const response =
      fieldModal.mode === "create"
        ? await createMailerLiteField(fieldModal.name.trim(), fieldModal.type)
        : await updateMailerLiteField(fieldModal.field?.id, fieldModal.name.trim())
    if (response?.error) {
      setError(response.error)
      return
    }
    closeFieldModal()
    fetchFields()
  }

  const handleDeleteField = async (field) => {
    if (!confirm(`Eliminare il campo "${field.name}"?`)) return
    const response = await deleteMailerLiteField(field.id)
    if (response?.error) {
      setError(response.error)
      return
    }
    fetchFields()
  }

  const openSegmentModal = (segment) => {
    setSegmentModal({
      open: true,
      segment,
      name: segment?.name || "",
    })
  }

  const closeSegmentModal = () => {
    setSegmentModal({ open: false, segment: null, name: "" })
  }

  const submitSegmentModal = async () => {
    if (!segmentModal.name.trim()) {
      setError("Inserisci un nome segmento valido.")
      return
    }
    const response = await updateMailerLiteSegment(
      segmentModal.segment?.id,
      segmentModal.name.trim()
    )
    if (response?.error) {
      setError(response.error)
      return
    }
    closeSegmentModal()
    fetchSegments()
  }

  const handleDeleteSegment = async (segment) => {
    if (!confirm(`Eliminare il segmento "${segment.name}"?`)) return
    const response = await deleteMailerLiteSegment(segment.id)
    if (response?.error) {
      setError(response.error)
      return
    }
    fetchSegments()
  }

  const nameFor = (subscriber) => {
    const fields = subscriber.fields || {}
    const parts = [fields.name, fields.last_name].filter(Boolean)
    return parts.length ? parts.join(" ") : "-"
  }

  const formatDate = (value) => {
    if (!value) return "-"
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return value
    return date.toLocaleDateString("it-IT", {
      year: "numeric",
      month: "short",
      day: "2-digit",
    })
  }

  const normalizeDateInput = (value) => {
    if (!value || typeof value !== "string") return ""
    const trimmed = value.trim()
    if (!trimmed) return ""
    const datePart = trimmed.split(" ")[0]
    if (/^\d{4}-\d{2}-\d{2}$/.test(datePart)) return datePart
    const parsed = new Date(trimmed)
    if (Number.isNaN(parsed.getTime())) return ""
    const yyyy = parsed.getFullYear()
    const mm = String(parsed.getMonth() + 1).padStart(2, "0")
    const dd = String(parsed.getDate()).padStart(2, "0")
    return `${yyyy}-${mm}-${dd}`
  }


  return (
    <motion.div
      className="space-y-6 pb-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Button variant="ghost" onClick={() => router.push(routes.admin.dashboard)}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Torna admin
          </Button>
          <h1 className="text-3xl md:text-4xl font-bold gradient-text mt-2">Subscribers</h1>
          <p className="text-gray-300">Gestisci iscritti, gruppi e filtri MailerLite.</p>
        </div>
        <div className="flex gap-2 w-full md:w-auto">
          <Button
            variant="outline"
            onClick={fetchSubscribers}
            disabled={loading}
            className="flex-1 md:flex-none bg-transparent"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            <span className="ml-2">Aggiorna</span>
          </Button>
          <Button onClick={openCreateDialog} className="flex-1 md:flex-none">
            <Plus className="h-4 w-4 mr-2" /> Nuovo subscriber
          </Button>
        </div>
      </div>

      <Tabs defaultValue="subscribers" className="w-full">
        <TabsList className="w-full justify-start gap-8 border-b border-neutral-800 bg-transparent p-0">
          {[
            { value: "subscribers", label: "All subscribers" },
            { value: "segments", label: "Segments" },
            { value: "groups", label: "Groups" },
            { value: "fields", label: "Fields" },
          ].map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="relative rounded-none px-0 pb-3 text-base font-semibold text-neutral-400 data-[state=active]:text-white data-[state=active]:shadow-none data-[state=active]:after:absolute data-[state=active]:after:left-0 data-[state=active]:after:right-0 data-[state=active]:after:bottom-0 data-[state=active]:after:h-[2px] data-[state=active]:after:bg-emerald-400"
            >
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="subscribers" className="mt-6 space-y-6">
          <Card className="border-neutral-800 bg-neutral-900/60">
            <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-white">Filtri</CardTitle>
                <p className="text-sm text-neutral-400">
                  Cerca per email o nome e filtra lo stato.
                </p>
              </div>
              <div className="flex items-center gap-2 text-sm text-neutral-400">
                {groupsLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <span>{groups.length} gruppi</span>
                )}
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-3">
              <Input
                placeholder="Cerca email, nome, azienda..."
                value={filters.search}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, search: event.target.value }))
                }
              />
              <Select
                value={filters.status}
                onValueChange={(value) => setFilters((prev) => ({ ...prev, status: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Stato" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti gli stati</SelectItem>
                  {STATUS_OPTIONS.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={filters.groupId}
                onValueChange={(value) => {
                  setFilters((prev) => ({ ...prev, groupId: value }))
                  setCursor("")
                  setGroupPage(1)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Gruppo" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tutti i gruppi</SelectItem>
                  <SelectItem value="none">Senza gruppo</SelectItem>
                  {groups.map((group) => (
                    <SelectItem key={group.id} value={String(group.id)}>
                      {group.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Card className="border-neutral-800 bg-neutral-900/60">
            <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-white">Lista subscribers</CardTitle>
                <p className="text-sm text-neutral-400">
                  {filteredSubscribers.length} risultati nella pagina corrente.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  className="bg-transparent"
                  disabled={
                    filters.groupId !== "all" && filters.groupId !== "none"
                      ? groupPage === 1
                      : !meta?.prev_cursor
                  }
                  onClick={() => {
                    if (filters.groupId !== "all" && filters.groupId !== "none") {
                      setGroupPage((prev) => Math.max(1, prev - 1))
                      return
                    }
                    setCursor(meta?.prev_cursor || "")
                  }}
                >
                  Prev
                </Button>
                <Button
                  variant="outline"
                  className="bg-transparent"
                  disabled={
                    filters.groupId !== "all" && filters.groupId !== "none"
                      ? !groupHasNext
                      : !meta?.next_cursor
                  }
                  onClick={() => {
                    if (filters.groupId !== "all" && filters.groupId !== "none") {
                      setGroupPage((prev) => prev + 1)
                      return
                    }
                    setCursor(meta?.next_cursor || "")
                  }}
                >
                  Next
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Nome</TableHead>
                      <TableHead>Stato</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Iscrizione</TableHead>
                      <TableHead>Open</TableHead>
                      <TableHead>Click</TableHead>
                      <TableHead className="text-right">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {loading ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-10 text-neutral-400">
                          <Loader2 className="mx-auto mb-2 h-6 w-6 animate-spin" />
                          Caricamento subscribers...
                        </TableCell>
                      </TableRow>
                    ) : filteredSubscribers.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="text-center py-10 text-neutral-400">
                          Nessun subscriber trovato.
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredSubscribers.map((subscriber) => (
                        <TableRow key={subscriber.id}>
                          <TableCell className="font-medium text-white">
                            {subscriber.email}
                          </TableCell>
                          <TableCell>{nameFor(subscriber)}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className="border-emerald-500/40 text-emerald-300">
                              {subscriber.status || "n/a"}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-neutral-400">
                            {subscriber.source || "-"}
                          </TableCell>
                          <TableCell>{formatDate(subscriber.subscribed_at)}</TableCell>
                          <TableCell className="text-neutral-400">{subscriber.opens_count ?? 0}</TableCell>
                          <TableCell className="text-neutral-400">{subscriber.clicks_count ?? 0}</TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu modal={false}>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-48">
                                <DropdownMenuItem onSelect={() => openEditDialog(subscriber)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Modifica
                                </DropdownMenuItem>
                                <DropdownMenuItem onSelect={() => openGroupDialog(subscriber, "assign")}>
                                  <UserPlus className="mr-2 h-4 w-4" />
                                  Aggiungi a gruppo
                                </DropdownMenuItem>
                                <DropdownMenuItem onSelect={() => openGroupDialog(subscriber, "remove")}>
                                  <UserMinus className="mr-2 h-4 w-4" />
                                  Rimuovi da gruppo
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onSelect={() => handleDelete(subscriber)}
                                  className="text-red-400 focus:text-red-400"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Elimina
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="segments" className="mt-6 space-y-6">
          <Card className="border-neutral-800 bg-neutral-900/60">
            <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-white">Segmenti</CardTitle>
                <p className="text-sm text-neutral-400">
                  I segmenti sono gestiti da regole in MailerLite.
                </p>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" className="bg-transparent" onClick={fetchSegments}>
                  <RefreshCw className="h-4 w-4" />
                  <span className="ml-2">Aggiorna</span>
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>ID</TableHead>
                      <TableHead className="text-right">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {segments.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center py-10 text-neutral-400">
                          Nessun segmento trovato.
                        </TableCell>
                      </TableRow>
                    ) : (
                      segments.map((segment) => (
                        <TableRow key={segment.id}>
                          <TableCell className="font-medium text-white">{segment.name}</TableCell>
                          <TableCell className="text-neutral-400">{segment.id}</TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu modal={false}>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-40">
                                <DropdownMenuItem onClick={() => openSegmentModal(segment)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Rinomina
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => handleDeleteSegment(segment)}
                                  className="text-red-400 focus:text-red-400"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Elimina
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="groups" className="mt-6 space-y-6">
          <Card className="border-neutral-800 bg-neutral-900/60">
            <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-white">Gruppi</CardTitle>
                <p className="text-sm text-neutral-400">Gestisci i gruppi MailerLite.</p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="bg-transparent"
                  onClick={fetchGroups}
                  disabled={groupsLoading}
                >
                  {groupsLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  <span className="ml-2">Aggiorna</span>
                </Button>
                <Button onClick={() => openGroupModal("create")}>
                  <Plus className="h-4 w-4 mr-2" />
                  Nuovo gruppo
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>ID</TableHead>
                      <TableHead className="text-right">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groupsLoading ? (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center py-10 text-neutral-400">
                          <Loader2 className="mx-auto mb-2 h-6 w-6 animate-spin" />
                          Caricamento gruppi...
                        </TableCell>
                      </TableRow>
                    ) : groups.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} className="text-center py-10 text-neutral-400">
                          Nessun gruppo trovato.
                        </TableCell>
                      </TableRow>
                    ) : (
                      groups.map((group) => (
                        <TableRow key={group.id}>
                          <TableCell className="font-medium text-white">{group.name}</TableCell>
                          <TableCell className="text-neutral-400">{group.id}</TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu modal={false}>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-40">
                                <DropdownMenuItem onClick={() => openGroupModal("edit", group)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Rinomina
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => handleDeleteGroup(group)}
                                  className="text-red-400 focus:text-red-400"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Elimina
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fields" className="mt-6 space-y-6">
          <Card className="border-neutral-800 bg-neutral-900/60">
            <CardHeader className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
              <div>
                <CardTitle className="text-white">Campi personalizzati</CardTitle>
                <p className="text-sm text-neutral-400">Crea e gestisci i custom fields.</p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="bg-transparent"
                  onClick={fetchFields}
                >
                  <RefreshCw className="h-4 w-4" />
                  <span className="ml-2">Aggiorna</span>
                </Button>
                <Button onClick={() => openFieldModal("create")}>
                  <Plus className="h-4 w-4 mr-2" />
                  Nuovo campo
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nome</TableHead>
                      <TableHead>Tipo</TableHead>
                      <TableHead>ID</TableHead>
                      <TableHead className="text-right">Azioni</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center py-10 text-neutral-400">
                          Nessun campo trovato.
                        </TableCell>
                      </TableRow>
                    ) : (
                      fields.map((field) => (
                        <TableRow key={field.id}>
                          <TableCell className="font-medium text-white">{field.name}</TableCell>
                          <TableCell className="text-neutral-400">{field.type}</TableCell>
                          <TableCell className="text-neutral-400">{field.id}</TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu modal={false}>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreVertical className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end" className="w-40">
                                <DropdownMenuItem onClick={() => openFieldModal("edit", field)}>
                                  <Pencil className="mr-2 h-4 w-4" />
                                  Rinomina
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => handleDeleteField(field)}
                                  className="text-red-400 focus:text-red-400"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Elimina
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog
        open={isDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            blurActiveElement()
            closeDialog()
            return
          }
          setDialogOpen(true)
        }}
      >
        <DialogContent className="border-neutral-800 bg-neutral-950 text-white w-[95vw] max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{isEditMode ? "Modifica subscriber" : "Nuovo subscriber"}</DialogTitle>
            <DialogDescription className="text-neutral-400">
              {isEditMode
                ? "Aggiorna i dati principali del subscriber."
                : "Inserisci i dati per creare un nuovo subscriber."}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={submitSubscriber} className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-neutral-300">Email</label>
              <Input
                type="email"
                value={form.email}
                onChange={(event) => handleFormChange("email", event.target.value)}
                disabled={isEditMode}
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Nome</label>
                <Input
                  value={form.firstName}
                  onChange={(event) => handleFormChange("firstName", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Cognome</label>
                <Input
                  value={form.lastName}
                  onChange={(event) => handleFormChange("lastName", event.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Azienda</label>
                <Input
                  value={form.company}
                  onChange={(event) => handleFormChange("company", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Citta</label>
                <Input
                  value={form.city}
                  onChange={(event) => handleFormChange("city", event.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Paese</label>
                <Input
                  value={form.country}
                  onChange={(event) => handleFormChange("country", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Telefono</label>
                <Input
                  value={form.phone}
                  onChange={(event) => handleFormChange("phone", event.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Provincia/Stato</label>
                <Input
                  value={form.state}
                  onChange={(event) => handleFormChange("state", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">CAP</label>
                <Input
                  value={form.zip}
                  onChange={(event) => handleFormChange("zip", event.target.value)}
                />
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Gender</label>
                <Input
                  value={form.gender}
                  onChange={(event) => handleFormChange("gender", event.target.value)}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Birthdate</label>
                <Input
                  type="date"
                  value={form.birthdate}
                  onChange={(event) => handleFormChange("birthdate", event.target.value)}
                />
                {isEditMode && !form.birthdate && (
                  <p className="text-xs text-neutral-500">Nessuna data di nascita presente.</p>
                )}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Stato</label>
                <Select value={form.status} onValueChange={(value) => handleFormChange("status", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="z-[400]">
                    {STATUS_OPTIONS.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {!isEditMode && (
                <div className="space-y-2">
                  <label className="text-sm text-neutral-300">Gruppo iniziale</label>
                  <Select value={form.groupId} onValueChange={(value) => handleFormChange("groupId", value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Nessun gruppo" />
                  </SelectTrigger>
                  <SelectContent className="z-[400]">
                    <SelectItem value="none">Nessun gruppo</SelectItem>
                    {groups.map((group) => (
                      <SelectItem key={group.id} value={String(group.id)}>
                        {group.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
            <DialogFooter>
              <Button type="button" variant="ghost" onClick={closeDialog}>
                Annulla
              </Button>
              <Button type="submit">{isEditMode ? "Salva" : "Crea subscriber"}</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog
        open={groupModal.open}
        onOpenChange={(open) => {
          if (!open) {
            blurActiveElement()
            closeGroupModal()
            return
          }
          setGroupModal((prev) => ({ ...prev, open }))
        }}
      >
        <DialogContent className="border-neutral-800 bg-neutral-950 text-white w-[95vw] max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {groupModal.mode === "create" ? "Nuovo gruppo" : "Rinomina gruppo"}
            </DialogTitle>
            <DialogDescription className="text-neutral-400">
              {groupModal.mode === "create"
                ? "Crea un nuovo gruppo per i tuoi subscribers."
                : "Aggiorna il nome del gruppo selezionato."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label className="text-sm text-neutral-300">Nome gruppo</label>
            <Input
              value={groupModal.name}
              onChange={(event) =>
                setGroupModal((prev) => ({ ...prev, name: event.target.value }))
              }
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={closeGroupModal}>
              Annulla
            </Button>
            <Button onClick={submitGroupModal}>
              {groupModal.mode === "create" ? "Crea gruppo" : "Salva"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={fieldModal.open}
        onOpenChange={(open) => {
          if (!open) {
            blurActiveElement()
            closeFieldModal()
            return
          }
          setFieldModal((prev) => ({ ...prev, open }))
        }}
      >
        <DialogContent className="border-neutral-800 bg-neutral-950 text-white w-[95vw] max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {fieldModal.mode === "create" ? "Nuovo campo" : "Rinomina campo"}
            </DialogTitle>
            <DialogDescription className="text-neutral-400">
              {fieldModal.mode === "create"
                ? "Aggiungi un nuovo campo personalizzato."
                : "Aggiorna il nome del campo selezionato."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm text-neutral-300">Nome campo</label>
              <Input
                value={fieldModal.name}
                onChange={(event) =>
                  setFieldModal((prev) => ({ ...prev, name: event.target.value }))
                }
              />
            </div>
            {fieldModal.mode === "create" && (
              <div className="space-y-2">
                <label className="text-sm text-neutral-300">Tipo campo</label>
                <Select
                  value={fieldModal.type}
                  onValueChange={(value) =>
                    setFieldModal((prev) => ({ ...prev, type: value }))
                  }
                >
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona tipo" />
                </SelectTrigger>
                <SelectContent className="z-[400]">
                  {FIELD_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={closeFieldModal}>
              Annulla
            </Button>
            <Button onClick={submitFieldModal}>
              {fieldModal.mode === "create" ? "Crea campo" : "Salva"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog
        open={segmentModal.open}
        onOpenChange={(open) => {
          if (!open) {
            blurActiveElement()
            closeSegmentModal()
            return
          }
          setSegmentModal((prev) => ({ ...prev, open }))
        }}
      >
        <DialogContent className="border-neutral-800 bg-neutral-950 text-white w-[95vw] max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Rinomina segmento</DialogTitle>
            <DialogDescription className="text-neutral-400">
              Aggiorna il nome del segmento selezionato.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <label className="text-sm text-neutral-300">Nome segmento</label>
            <Input
              value={segmentModal.name}
              onChange={(event) =>
                setSegmentModal((prev) => ({ ...prev, name: event.target.value }))
              }
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={closeSegmentModal}>
              Annulla
            </Button>
            <Button onClick={submitSegmentModal}>
              Salva
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog
        open={groupDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            blurActiveElement()
            closeGroupDialog()
            return
          }
          setGroupDialog((prev) => ({ ...prev, open }))
        }}
      >
        <DialogContent className="border-neutral-800 bg-neutral-950 text-white w-[95vw] max-w-md max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {groupDialog.mode === "assign" ? "Aggiungi a gruppo" : "Rimuovi da gruppo"}
            </DialogTitle>
            <DialogDescription className="text-neutral-400">
              Seleziona il gruppo per {groupDialog.subscriber?.email || "subscriber"}.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Select
              value={groupDialog.groupId}
              onValueChange={(value) => setGroupDialog((prev) => ({ ...prev, groupId: value }))}
            >
            <SelectTrigger>
              <SelectValue placeholder="Seleziona gruppo" />
            </SelectTrigger>
            <SelectContent className="z-[400]">
              <SelectItem value="none">Seleziona gruppo</SelectItem>
              {groups.map((group) => (
                <SelectItem key={group.id} value={String(group.id)}>
                  {group.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={closeGroupDialog}>
              Annulla
            </Button>
            <Button onClick={submitGroupDialog}>
              {groupDialog.mode === "assign" ? "Aggiungi" : "Rimuovi"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  )
}
