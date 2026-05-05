"use client"

import { useEffect, useState, useCallback } from "react"
import { motion } from "framer-motion"
import {
  Loader2,
  MoreVertical,
  Plus,
  RefreshCw,
  Trash2,
  UserMinus,
  UserPlus,
  Pencil,
  Users,
  Info,
} from "lucide-react"

import { routes } from "@/config/routes"
import {
  listSenderSubscribers,
  getSenderSubscriber,
  upsertSenderSubscriber,
  updateSenderSubscriber,
  deleteSenderSubscriber,
  addSenderSubscriberToGroup,
  removeSenderSubscriberFromGroup,
  listSenderGroups,
  createSenderGroup,
  renameSenderGroup,
  deleteSenderGroup,
  listSenderGroupSubscribers,
  listSenderSegments,
  listSenderSegmentSubscribers,
  listSenderFields,
  createSenderField,
  deleteSenderField,
} from "@/services/admin/sender"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
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
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { AdminPageHeader } from "@/components/admin/AdminPageChrome"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const normalizeList = (res) => {
  if (Array.isArray(res)) return res
  if (res && Array.isArray(res.data)) return res.data
  return []
}

const EMPTY_SUBSCRIBER_FORM = {
  email: "",
  firstname: "",
  lastname: "",
  phone: "",
  groupId: "",
}

const EMPTY_FIELD_FORM = {
  title: "",
  type: "string",
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function SubscribersPage() {
  // ---- Global error state ----
  const [error, setError] = useState("")

  // ---- Subscribers tab state ----
  const [subscribers, setSubscribers] = useState([])
  const [subsLoading, setSubsLoading] = useState(false)
  const [subSearch, setSubSearch] = useState("")

  const [subDialogOpen, setSubDialogOpen] = useState(false)
  const [subEditMode, setSubEditMode] = useState(false)
  const [subForm, setSubForm] = useState(EMPTY_SUBSCRIBER_FORM)

  const [assignDialogOpen, setAssignDialogOpen] = useState(false)
  const [assignTarget, setAssignTarget] = useState(null) // { email }
  const [assignGroupId, setAssignGroupId] = useState("")
  const [assignGroupsLoading, setAssignGroupsLoading] = useState(false)

  const [removeDialogOpen, setRemoveDialogOpen] = useState(false)
  const [removeTarget, setRemoveTarget] = useState(null) // { email, groups }
  const [removeGroupId, setRemoveGroupId] = useState("")

  // ---- Groups tab state ----
  const [groups, setGroups] = useState([])
  const [groupsLoading, setGroupsLoading] = useState(false)

  const [newGroupDialogOpen, setNewGroupDialogOpen] = useState(false)
  const [newGroupTitle, setNewGroupTitle] = useState("")

  const [renameGroupDialogOpen, setRenameGroupDialogOpen] = useState(false)
  const [renameTarget, setRenameTarget] = useState(null)
  const [renameTitle, setRenameTitle] = useState("")

  const [groupSubsDialogOpen, setGroupSubsDialogOpen] = useState(false)
  const [groupSubsTarget, setGroupSubsTarget] = useState(null) // { id, title }
  const [groupSubsList, setGroupSubsList] = useState([])
  const [groupSubsLoading, setGroupSubsLoading] = useState(false)

  // ---- Segments tab state ----
  const [segments, setSegments] = useState([])
  const [segmentsLoading, setSegmentsLoading] = useState(false)

  const [segSubsDialogOpen, setSegSubsDialogOpen] = useState(false)
  const [segSubsTarget, setSegSubsTarget] = useState(null) // { id, title }
  const [segSubsList, setSegSubsList] = useState([])
  const [segSubsLoading, setSegSubsLoading] = useState(false)

  // ---- Fields tab state ----
  const [fields, setFields] = useState([])
  const [fieldsLoading, setFieldsLoading] = useState(false)

  const [fieldDialogOpen, setFieldDialogOpen] = useState(false)
  const [fieldForm, setFieldForm] = useState(EMPTY_FIELD_FORM)
  const [fieldSaving, setFieldSaving] = useState(false)

  // ---- Action saving flags ----
  const [subSaving, setSubSaving] = useState(false)
  const [groupSaving, setGroupSaving] = useState(false)
  const [assignSaving, setAssignSaving] = useState(false)

  // ---------------------------------------------------------------------------
  // Data loaders
  // ---------------------------------------------------------------------------

  const loadSubscribers = useCallback(async () => {
    setSubsLoading(true)
    setError("")
    try {
      const res = await listSenderSubscribers({ limit: 200 })
      setSubscribers(normalizeList(res))
    } catch (e) {
      console.error(e)
      setError("Errore nel caricamento dei subscriber.")
    } finally {
      setSubsLoading(false)
    }
  }, [])

  const loadGroups = useCallback(async () => {
    setGroupsLoading(true)
    try {
      const res = await listSenderGroups()
      setGroups(normalizeList(res))
    } catch (e) {
      console.error(e)
      setError("Errore nel caricamento dei gruppi.")
    } finally {
      setGroupsLoading(false)
    }
  }, [])

  const loadSegments = useCallback(async () => {
    setSegmentsLoading(true)
    try {
      const res = await listSenderSegments()
      setSegments(normalizeList(res))
    } catch (e) {
      console.error(e)
      setError("Errore nel caricamento dei segmenti.")
    } finally {
      setSegmentsLoading(false)
    }
  }, [])

  const loadFields = useCallback(async () => {
    setFieldsLoading(true)
    try {
      const res = await listSenderFields()
      setFields(normalizeList(res))
    } catch (e) {
      console.error(e)
      setError("Errore nel caricamento dei campi.")
    } finally {
      setFieldsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSubscribers()
    loadGroups()
    loadSegments()
    loadFields()
  }, [loadSubscribers, loadGroups, loadSegments, loadFields])

  // ---------------------------------------------------------------------------
  // Subscriber search (single lookup by email)
  // ---------------------------------------------------------------------------

  const handleSubSearch = useCallback(async () => {
    if (!subSearch.trim()) {
      loadSubscribers()
      return
    }
    setSubsLoading(true)
    setError("")
    try {
      const res = await getSenderSubscriber(subSearch.trim())
      const result = res?.data ?? res
      if (result && result.email) {
        setSubscribers([result])
      } else {
        setSubscribers([])
      }
    } catch (e) {
      console.error(e)
      setError("Subscriber non trovato.")
      setSubscribers([])
    } finally {
      setSubsLoading(false)
    }
  }, [subSearch, loadSubscribers])

  // ---------------------------------------------------------------------------
  // Subscriber CRUD
  // ---------------------------------------------------------------------------

  const openNewSubDialog = () => {
    setSubEditMode(false)
    setSubForm(EMPTY_SUBSCRIBER_FORM)
    setSubDialogOpen(true)
  }

  const openEditSubDialog = (sub) => {
    setSubEditMode(true)
    setSubForm({
      email: sub.email ?? "",
      firstname: sub.firstname ?? "",
      lastname: sub.lastname ?? "",
      phone: sub.phone ?? "",
      groupId: "",
    })
    setSubDialogOpen(true)
  }

  const closeSubDialog = () => {
    setSubDialogOpen(false)
    setSubForm(EMPTY_SUBSCRIBER_FORM)
  }

  const handleSubSubmit = async (e) => {
    e.preventDefault()
    if (!subForm.email) return
    setSubSaving(true)
    setError("")
    try {
      if (subEditMode) {
        await updateSenderSubscriber({
          email: subForm.email,
          firstname: subForm.firstname,
          lastname: subForm.lastname,
          phone: subForm.phone,
        })
      } else {
        const payload = {
          email: subForm.email,
          firstname: subForm.firstname,
          lastname: subForm.lastname,
          phone: subForm.phone,
        }
        if (subForm.groupId) payload.groups = [subForm.groupId]
        await upsertSenderSubscriber(payload)
      }
      await loadSubscribers()
      closeSubDialog()
    } catch (err) {
      console.error(err)
      setError("Errore nel salvataggio del subscriber.")
    } finally {
      setSubSaving(false)
    }
  }

  const handleDeleteSub = async (email) => {
    if (!confirm(`Eliminare il subscriber ${email}?`)) return
    setError("")
    try {
      await deleteSenderSubscriber(email)
      setSubscribers((prev) => prev.filter((s) => s.email !== email))
    } catch (err) {
      console.error(err)
      setError("Errore nell'eliminazione del subscriber.")
    }
  }

  // ---------------------------------------------------------------------------
  // Assign / Remove from group
  // ---------------------------------------------------------------------------

  const openAssignDialog = async (sub) => {
    setAssignTarget(sub)
    setAssignGroupId("")
    setAssignDialogOpen(true)
    // Always reload groups fresh when dialog opens
    setAssignGroupsLoading(true)
    try {
      const res = await listSenderGroups()
      setGroups(normalizeList(res))
    } catch {
      // keep existing groups if any
    } finally {
      setAssignGroupsLoading(false)
    }
  }

  const handleAssignGroup = async () => {
    if (!assignTarget || !assignGroupId) return
    setAssignSaving(true)
    setError("")
    try {
      await addSenderSubscriberToGroup(assignTarget.email, assignGroupId)
      await loadSubscribers()
      setAssignDialogOpen(false)
    } catch (err) {
      console.error(err)
      setError("Errore nell'assegnazione al gruppo.")
    } finally {
      setAssignSaving(false)
    }
  }

  const openRemoveDialog = (sub) => {
    setRemoveTarget(sub)
    setRemoveGroupId("")
    setRemoveDialogOpen(true)
  }

  const handleRemoveFromGroup = async () => {
    if (!removeTarget || !removeGroupId) return
    setAssignSaving(true)
    setError("")
    try {
      await removeSenderSubscriberFromGroup(removeTarget.email, removeGroupId)
      await loadSubscribers()
      setRemoveDialogOpen(false)
    } catch (err) {
      console.error(err)
      setError("Errore nella rimozione dal gruppo.")
    } finally {
      setAssignSaving(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Groups CRUD
  // ---------------------------------------------------------------------------

  const handleCreateGroup = async (e) => {
    e.preventDefault()
    if (!newGroupTitle.trim()) return
    setGroupSaving(true)
    setError("")
    try {
      await createSenderGroup(newGroupTitle.trim())
      await loadGroups()
      setNewGroupTitle("")
      setNewGroupDialogOpen(false)
    } catch (err) {
      console.error(err)
      setError("Errore nella creazione del gruppo.")
    } finally {
      setGroupSaving(false)
    }
  }

  const openRenameDialog = (group) => {
    setRenameTarget(group)
    setRenameTitle(group.title ?? "")
    setRenameGroupDialogOpen(true)
  }

  const handleRenameGroup = async (e) => {
    e.preventDefault()
    if (!renameTarget || !renameTitle.trim()) return
    setGroupSaving(true)
    setError("")
    try {
      await renameSenderGroup(renameTarget.id, renameTitle.trim())
      await loadGroups()
      setRenameGroupDialogOpen(false)
    } catch (err) {
      console.error(err)
      setError("Errore nel rinominare il gruppo.")
    } finally {
      setGroupSaving(false)
    }
  }

  const handleDeleteGroup = async (group) => {
    if (!confirm(`Eliminare il gruppo "${group.title}"?`)) return
    setError("")
    try {
      await deleteSenderGroup(group.id)
      setGroups((prev) => prev.filter((g) => g.id !== group.id))
    } catch (err) {
      console.error(err)
      setError("Errore nell'eliminazione del gruppo.")
    }
  }

  const openGroupSubsDialog = async (group) => {
    setGroupSubsTarget(group)
    setGroupSubsList([])
    setGroupSubsDialogOpen(true)
    setGroupSubsLoading(true)
    try {
      const res = await listSenderGroupSubscribers(group.id)
      setGroupSubsList(normalizeList(res))
    } catch (err) {
      console.error(err)
      setError("Errore nel caricamento dei subscriber del gruppo.")
    } finally {
      setGroupSubsLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Segments
  // ---------------------------------------------------------------------------

  const openSegSubsDialog = async (segment) => {
    setSegSubsTarget(segment)
    setSegSubsList([])
    setSegSubsDialogOpen(true)
    setSegSubsLoading(true)
    try {
      const res = await listSenderSegmentSubscribers(segment.id)
      setSegSubsList(normalizeList(res))
    } catch (err) {
      console.error(err)
      setError("Errore nel caricamento dei subscriber del segmento.")
    } finally {
      setSegSubsLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Fields CRUD
  // ---------------------------------------------------------------------------

  const handleCreateField = async (e) => {
    e.preventDefault()
    if (!fieldForm.title.trim()) return
    setFieldSaving(true)
    setError("")
    try {
      await createSenderField({ title: fieldForm.title.trim(), type: fieldForm.type })
      await loadFields()
      setFieldForm(EMPTY_FIELD_FORM)
      setFieldDialogOpen(false)
    } catch (err) {
      console.error(err)
      setError("Errore nella creazione del campo.")
    } finally {
      setFieldSaving(false)
    }
  }

  const handleDeleteField = async (field) => {
    if (!confirm(`Eliminare il campo "${field.title}"? Verrà rimosso da tutti i subscriber.`)) return
    setError("")
    try {
      await deleteSenderField(field.id)
      setFields((prev) => prev.filter((f) => f.id !== field.id))
    } catch (err) {
      console.error(err)
      setError("Errore nell'eliminazione del campo.")
    }
  }

  // ---------------------------------------------------------------------------
  // Render helpers
  // ---------------------------------------------------------------------------

  const renderStatusBadge = (status) => {
    const s = typeof status === "string" ? status : null
    if (s === "active") {
      return <Badge className="bg-green-600 text-white">Attivo</Badge>
    }
    return <Badge variant="secondary">{s ?? "—"}</Badge>
  }

  const renderGroupNames = (sub) => {
    const raw = sub.groups
    const gs = Array.isArray(raw) ? raw : []
    if (!gs.length) return <span className="text-gray-500 text-sm">—</span>
    return (
      <div className="flex flex-wrap gap-1">
        {gs.map((g, i) => {
          const label =
            typeof g === "string" ? g :
            typeof g?.title === "string" ? g.title :
            typeof g?.name === "string" ? g.name :
            g?.id ? String(g.id) : `#${i + 1}`
          return (
            <Badge key={g?.id ?? i} variant="outline" className="text-xs">
              {label}
            </Badge>
          )
        })}
      </div>
    )
  }

  const safeStr = (v) => (typeof v === "string" || typeof v === "number") ? v : "—"

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-6 pb-8"
      >
        <AdminPageHeader
          title="CRM Sender"
          description="Gestisci subscriber, gruppi, segmenti e campi."
          backHref={routes.admin.dashboard}
          backLabel="Torna alla dashboard"
        />

        {/* Global error */}
        {error && (
          <p className="text-red-500 text-sm font-medium">{error}</p>
        )}

        {/* Tabs */}
        <Tabs defaultValue="subscribers">
          <TabsList className="mb-4 flex-wrap h-auto">
            <TabsTrigger value="subscribers">Subscriber</TabsTrigger>
            <TabsTrigger value="groups">Gruppi</TabsTrigger>
            <TabsTrigger value="segments">Segmenti</TabsTrigger>
            <TabsTrigger value="fields">Campi</TabsTrigger>
          </TabsList>

          {/* ================================================================
              TAB 1 — SUBSCRIBERS
          ================================================================ */}
          <TabsContent value="subscribers" className="space-y-4">
            {/* Toolbar */}
            <div className="flex flex-col sm:flex-row gap-2">
              <Input
                value={subSearch}
                onChange={(e) => setSubSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSubSearch()}
                placeholder="Cerca per email (Invio per cercare)…"
                className="flex-1"
              />
              <Button variant="outline" onClick={handleSubSearch} disabled={subsLoading}>
                {subsLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Cerca"
                )}
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => { setSubSearch(""); loadSubscribers() }}
                disabled={subsLoading}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={openNewSubDialog}>
                <Plus className="mr-2 h-4 w-4" /> Nuovo subscriber
              </Button>
            </div>

            {/* Table */}
            <Card className="bg-zinc-900 border border-zinc-700">
              <CardContent className="p-0">
                {subsLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <>
                    {/* Desktop */}
                    <div className="hidden md:block overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Email</TableHead>
                            <TableHead>Nome</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Gruppi</TableHead>
                            <TableHead className="text-right">Azioni</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {subscribers.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                                Nessun subscriber trovato.
                              </TableCell>
                            </TableRow>
                          ) : (
                            subscribers.map((sub) => (
                              <TableRow key={sub.id ?? sub.email}>
                                <TableCell className="font-mono text-sm">{sub.email}</TableCell>
                                <TableCell>
                                  {sub.firstname || sub.lastname
                                    ? `${sub.firstname ?? ""} ${sub.lastname ?? ""}`.trim()
                                    : <span className="text-gray-500">—</span>
                                  }
                                </TableCell>
                                <TableCell>{renderStatusBadge(sub.status)}</TableCell>
                                <TableCell>{renderGroupNames(sub)}</TableCell>
                                <TableCell className="text-right space-x-1">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={() => openAssignDialog(sub)}
                                      >
                                        <UserPlus className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Assegna a gruppo</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={() => openRemoveDialog(sub)}
                                        disabled={!(sub.groups ?? []).length}
                                      >
                                        <UserMinus className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Rimuovi da gruppo</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={() => openEditSubDialog(sub)}
                                      >
                                        <Pencil className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Modifica</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        className="text-red-500"
                                        onClick={() => handleDeleteSub(sub.email)}
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Elimina</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </div>

                    {/* Mobile */}
                    <div className="block md:hidden space-y-3 p-4">
                      {subscribers.length === 0 ? (
                        <p className="text-center text-gray-500 py-8">Nessun subscriber trovato.</p>
                      ) : (
                        subscribers.map((sub) => (
                          <Card key={sub.id ?? sub.email} className="bg-zinc-800 border-zinc-700">
                            <CardHeader className="flex flex-row items-start justify-between gap-2 p-4">
                              <div className="min-w-0">
                                <p className="font-mono text-sm truncate">{sub.email}</p>
                                <p className="text-xs text-gray-400 mt-0.5">
                                  {sub.firstname || sub.lastname
                                    ? `${sub.firstname ?? ""} ${sub.lastname ?? ""}`.trim()
                                    : "—"
                                  }
                                </p>
                                <div className="mt-1 flex flex-wrap gap-1">
                                  {renderStatusBadge(sub.status)}
                                  {renderGroupNames(sub)}
                                </div>
                              </div>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="h-5 w-5" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => openAssignDialog(sub)}>
                                    <UserPlus className="mr-2 h-4 w-4" /> Assegna a gruppo
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => openRemoveDialog(sub)}
                                    disabled={!(sub.groups ?? []).length}
                                  >
                                    <UserMinus className="mr-2 h-4 w-4" /> Rimuovi da gruppo
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => openEditSubDialog(sub)}>
                                    <Pencil className="mr-2 h-4 w-4" /> Modifica
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => handleDeleteSub(sub.email)}
                                    className="text-red-500 focus:text-red-500"
                                  >
                                    <Trash2 className="mr-2 h-4 w-4" /> Elimina
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </CardHeader>
                          </Card>
                        ))
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ================================================================
              TAB 2 — GROUPS
          ================================================================ */}
          <TabsContent value="groups" className="space-y-4">
            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <Card className="bg-zinc-900 border border-zinc-700">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-gray-400">Totale Gruppi</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">{groups.length}</p>
                </CardContent>
              </Card>
            </div>

            {/* Toolbar */}
            <div className="flex justify-between items-center">
              <Button
                variant="ghost"
                size="icon"
                onClick={loadGroups}
                disabled={groupsLoading}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={() => { setNewGroupTitle(""); setNewGroupDialogOpen(true) }}>
                <Plus className="mr-2 h-4 w-4" /> Nuovo gruppo
              </Button>
            </div>

            {/* Table */}
            <Card className="bg-zinc-900 border border-zinc-700">
              <CardContent className="p-0">
                {groupsLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <>
                    {/* Desktop */}
                    <div className="hidden md:block overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Nome</TableHead>
                            <TableHead>Subscriber</TableHead>
                            <TableHead className="text-right">Azioni</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {groups.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={3} className="text-center py-8 text-gray-500">
                                Nessun gruppo trovato.
                              </TableCell>
                            </TableRow>
                          ) : (
                            groups.map((group, gi) => (
                              <TableRow key={group.id ?? gi}>
                                <TableCell className="font-medium">{group.title}</TableCell>
                                <TableCell>{group.count ?? "—"}</TableCell>
                                <TableCell className="text-right space-x-1">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={() => openGroupSubsDialog(group)}
                                      >
                                        <Users className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Vedi subscriber</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={() => openRenameDialog(group)}
                                      >
                                        <Pencil className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Rinomina</TooltipContent>
                                  </Tooltip>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        className="text-red-500"
                                        onClick={() => handleDeleteGroup(group)}
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Elimina</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </div>

                    {/* Mobile */}
                    <div className="block md:hidden space-y-3 p-4">
                      {groups.length === 0 ? (
                        <p className="text-center text-gray-500 py-8">Nessun gruppo trovato.</p>
                      ) : (
                        groups.map((group, gi) => (
                          <Card key={group.id ?? gi} className="bg-zinc-800 border-zinc-700">
                            <CardHeader className="flex flex-row items-center justify-between gap-2 p-4">
                              <div>
                                <p className="font-medium">{group.title}</p>
                                <p className="text-xs text-gray-400">{group.count ?? 0} subscriber</p>
                              </div>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="h-5 w-5" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem onClick={() => openGroupSubsDialog(group)}>
                                    <Users className="mr-2 h-4 w-4" /> Vedi subscriber
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => openRenameDialog(group)}>
                                    <Pencil className="mr-2 h-4 w-4" /> Rinomina
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => handleDeleteGroup(group)}
                                    className="text-red-500 focus:text-red-500"
                                  >
                                    <Trash2 className="mr-2 h-4 w-4" /> Elimina
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </CardHeader>
                          </Card>
                        ))
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ================================================================
              TAB 3 — SEGMENTS (read-only)
          ================================================================ */}
          <TabsContent value="segments" className="space-y-4">
            {/* Info banner */}
            <div className="flex items-start gap-3 rounded-lg border border-blue-700 bg-blue-950/40 p-4 text-blue-300">
              <Info className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <p className="text-sm">I segmenti sono gestiti dalla dashboard Sender.</p>
            </div>

            {/* Toolbar */}
            <div className="flex justify-end">
              <Button
                variant="ghost"
                size="icon"
                onClick={loadSegments}
                disabled={segmentsLoading}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>

            {/* Table */}
            <Card className="bg-zinc-900 border border-zinc-700">
              <CardContent className="p-0">
                {segmentsLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <>
                    {/* Desktop */}
                    <div className="hidden md:block overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Nome</TableHead>
                            <TableHead>Descrizione</TableHead>
                            <TableHead className="text-right">Azioni</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {segments.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={3} className="text-center py-8 text-gray-500">
                                Nessun segmento trovato.
                              </TableCell>
                            </TableRow>
                          ) : (
                            segments.map((seg, si) => (
                              <TableRow key={seg.id ?? si}>
                                <TableCell className="font-medium">{seg.title}</TableCell>
                                <TableCell className="text-gray-400 text-sm">
                                  {seg.description ?? "—"}
                                </TableCell>
                                <TableCell className="text-right">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        onClick={() => openSegSubsDialog(seg)}
                                      >
                                        <Users className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Vedi subscriber</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </div>

                    {/* Mobile */}
                    <div className="block md:hidden space-y-3 p-4">
                      {segments.length === 0 ? (
                        <p className="text-center text-gray-500 py-8">Nessun segmento trovato.</p>
                      ) : (
                        segments.map((seg, si) => (
                          <Card key={seg.id ?? si} className="bg-zinc-800 border-zinc-700">
                            <CardHeader className="flex flex-row items-center justify-between gap-2 p-4">
                              <div>
                                <p className="font-medium">{seg.title}</p>
                                {seg.description && (
                                  <p className="text-xs text-gray-400 mt-0.5">{seg.description}</p>
                                )}
                              </div>
                              <Button
                                size="icon"
                                variant="ghost"
                                onClick={() => openSegSubsDialog(seg)}
                              >
                                <Users className="h-5 w-5" />
                              </Button>
                            </CardHeader>
                          </Card>
                        ))
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ================================================================
              TAB 4 — FIELDS
          ================================================================ */}
          <TabsContent value="fields" className="space-y-4">
            {/* Toolbar */}
            <div className="flex justify-between items-center">
              <Button
                variant="ghost"
                size="icon"
                onClick={loadFields}
                disabled={fieldsLoading}
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button onClick={() => { setFieldForm(EMPTY_FIELD_FORM); setFieldDialogOpen(true) }}>
                <Plus className="mr-2 h-4 w-4" /> Nuovo campo
              </Button>
            </div>

            {/* Table */}
            <Card className="bg-zinc-900 border border-zinc-700">
              <CardContent className="p-0">
                {fieldsLoading ? (
                  <div className="flex justify-center items-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : (
                  <>
                    {/* Desktop */}
                    <div className="hidden md:block overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Titolo</TableHead>
                            <TableHead>Tipo</TableHead>
                            <TableHead className="text-right">Azioni</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {fields.length === 0 ? (
                            <TableRow>
                              <TableCell colSpan={3} className="text-center py-8 text-gray-500">
                                Nessun campo trovato.
                              </TableCell>
                            </TableRow>
                          ) : (
                            fields.map((field, fi) => (
                              <TableRow key={field.id ?? fi}>
                                <TableCell className="font-medium">{field.title}</TableCell>
                                <TableCell>
                                  <Badge variant="outline">{safeStr(field.type)}</Badge>
                                </TableCell>
                                <TableCell className="text-right">
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                        size="icon"
                                        variant="ghost"
                                        className="text-red-500"
                                        onClick={() => handleDeleteField(field)}
                                      >
                                        <Trash2 className="h-4 w-4" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>Elimina campo</TooltipContent>
                                  </Tooltip>
                                </TableCell>
                              </TableRow>
                            ))
                          )}
                        </TableBody>
                      </Table>
                    </div>

                    {/* Mobile */}
                    <div className="block md:hidden space-y-3 p-4">
                      {fields.length === 0 ? (
                        <p className="text-center text-gray-500 py-8">Nessun campo trovato.</p>
                      ) : (
                        fields.map((field, fi) => (
                          <Card key={field.id ?? fi} className="bg-zinc-800 border-zinc-700">
                            <CardHeader className="flex flex-row items-center justify-between gap-2 p-4">
                              <div>
                                <p className="font-medium">{field.title}</p>
                                <Badge variant="outline" className="mt-1 text-xs">{safeStr(field.type)}</Badge>
                              </div>
                              <Button
                                size="icon"
                                variant="ghost"
                                className="text-red-500"
                                onClick={() => handleDeleteField(field)}
                              >
                                <Trash2 className="h-5 w-5" />
                              </Button>
                            </CardHeader>
                          </Card>
                        ))
                      )}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Warning */}
            <p className="text-xs text-amber-400">
              Attenzione: eliminare un campo lo rimuove da tutti i subscriber.
            </p>
          </TabsContent>
        </Tabs>

        {/* ================================================================
            DIALOGS
        ================================================================ */}

        {/* --- Subscriber create / edit dialog --- */}
        <Dialog open={subDialogOpen} onOpenChange={(open) => { if (!open) closeSubDialog() }}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>{subEditMode ? "Modifica Subscriber" : "Nuovo Subscriber"}</DialogTitle>
              <DialogDescription>
                {subEditMode ? "Aggiorna i dati del subscriber." : "Compila i campi per aggiungere un nuovo subscriber."}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubSubmit} className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-1 block">Email *</label>
                <Input
                  type="email"
                  required
                  disabled={subEditMode}
                  value={subForm.email}
                  onChange={(e) => setSubForm((f) => ({ ...f, email: e.target.value }))}
                  placeholder="email@esempio.com"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Nome</label>
                <Input
                  value={subForm.firstname}
                  onChange={(e) => setSubForm((f) => ({ ...f, firstname: e.target.value }))}
                  placeholder="Mario"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Cognome</label>
                <Input
                  value={subForm.lastname}
                  onChange={(e) => setSubForm((f) => ({ ...f, lastname: e.target.value }))}
                  placeholder="Rossi"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Telefono</label>
                <Input
                  value={subForm.phone}
                  onChange={(e) => setSubForm((f) => ({ ...f, phone: e.target.value }))}
                  placeholder="+39 000 0000000"
                />
              </div>
              {!subEditMode && (
                <div>
                  <label className="text-sm font-medium mb-1 block">Gruppo (opzionale)</label>
                  <Select
                    value={subForm.groupId}
                    onValueChange={(v) => setSubForm((f) => ({ ...f, groupId: v }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Seleziona gruppo…" />
                    </SelectTrigger>
                    <SelectContent>
                      {groups.map((g) => (
                        <SelectItem key={g.id ?? g.title} value={String(g.id ?? g.title ?? "")}>
                          {g.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <DialogFooter className="pt-2">
                <Button type="button" variant="outline" onClick={closeSubDialog}>
                  Annulla
                </Button>
                <Button type="submit" disabled={subSaving}>
                  {subSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  {subEditMode ? "Salva" : "Crea"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* --- Assign to group dialog --- */}
        <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle>Assegna a Gruppo</DialogTitle>
              <DialogDescription>
                Seleziona il gruppo a cui aggiungere <strong>{assignTarget?.email}</strong>.
              </DialogDescription>
            </DialogHeader>
            {assignGroupsLoading ? (
              <div className="flex items-center gap-2 py-2 text-sm text-neutral-400">
                <Loader2 className="h-4 w-4 animate-spin" /> Caricamento gruppi...
              </div>
            ) : (
              <Select value={assignGroupId} onValueChange={setAssignGroupId}>
                <SelectTrigger>
                  <SelectValue placeholder={groups.length === 0 ? "Nessun gruppo disponibile" : "Seleziona gruppo…"} />
                </SelectTrigger>
                <SelectContent>
                  {groups.map((g, i) => (
                    <SelectItem key={g.id ?? g.title ?? i} value={String(g.id ?? g.title ?? i)}>
                      {g.title ?? g.name ?? String(g.id ?? "")}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <DialogFooter className="pt-2">
              <Button variant="outline" onClick={() => setAssignDialogOpen(false)}>
                Annulla
              </Button>
              <Button onClick={handleAssignGroup} disabled={!assignGroupId || assignSaving || assignGroupsLoading}>
                {assignSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Assegna
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* --- Remove from group dialog --- */}
        <Dialog open={removeDialogOpen} onOpenChange={setRemoveDialogOpen}>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle>Rimuovi da Gruppo</DialogTitle>
              <DialogDescription>
                Seleziona il gruppo da cui rimuovere <strong>{removeTarget?.email}</strong>.
              </DialogDescription>
            </DialogHeader>
            <Select value={removeGroupId} onValueChange={setRemoveGroupId}>
              <SelectTrigger>
                <SelectValue placeholder="Seleziona gruppo…" />
              </SelectTrigger>
              <SelectContent>
                {(removeTarget?.groups ?? []).map((g) => (
                  <SelectItem key={g.id ?? g.title} value={String(g.id ?? g.title ?? "")}>
                    {g.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <DialogFooter className="pt-2">
              <Button variant="outline" onClick={() => setRemoveDialogOpen(false)}>
                Annulla
              </Button>
              <Button
                variant="destructive"
                onClick={handleRemoveFromGroup}
                disabled={!removeGroupId || assignSaving}
              >
                {assignSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                Rimuovi
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* --- New group dialog --- */}
        <Dialog open={newGroupDialogOpen} onOpenChange={setNewGroupDialogOpen}>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle>Nuovo Gruppo</DialogTitle>
              <DialogDescription>Inserisci il nome del nuovo gruppo.</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateGroup} className="space-y-3">
              <Input
                required
                value={newGroupTitle}
                onChange={(e) => setNewGroupTitle(e.target.value)}
                placeholder="Nome gruppo…"
              />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setNewGroupDialogOpen(false)}>
                  Annulla
                </Button>
                <Button type="submit" disabled={groupSaving || !newGroupTitle.trim()}>
                  {groupSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Crea
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* --- Rename group dialog --- */}
        <Dialog open={renameGroupDialogOpen} onOpenChange={setRenameGroupDialogOpen}>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle>Rinomina Gruppo</DialogTitle>
              <DialogDescription>Inserisci il nuovo nome per il gruppo.</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleRenameGroup} className="space-y-3">
              <Input
                required
                value={renameTitle}
                onChange={(e) => setRenameTitle(e.target.value)}
                placeholder="Nuovo nome…"
              />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setRenameGroupDialogOpen(false)}>
                  Annulla
                </Button>
                <Button type="submit" disabled={groupSaving || !renameTitle.trim()}>
                  {groupSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Salva
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* --- Group subscribers dialog --- */}
        <Dialog open={groupSubsDialogOpen} onOpenChange={setGroupSubsDialogOpen}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Subscriber — {groupSubsTarget?.title}</DialogTitle>
              <DialogDescription>Elenco dei subscriber nel gruppo.</DialogDescription>
            </DialogHeader>
            {groupSubsLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : groupSubsList.length === 0 ? (
              <p className="text-center text-gray-500 py-8">Nessun subscriber in questo gruppo.</p>
            ) : (
              <div className="max-h-80 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Nome</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {groupSubsList.map((s) => (
                      <TableRow key={s.id ?? s.email}>
                        <TableCell className="font-mono text-sm">{s.email}</TableCell>
                        <TableCell>
                          {s.firstname || s.lastname
                            ? `${s.firstname ?? ""} ${s.lastname ?? ""}`.trim()
                            : "—"
                          }
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setGroupSubsDialogOpen(false)}>
                Chiudi
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* --- Segment subscribers dialog --- */}
        <Dialog open={segSubsDialogOpen} onOpenChange={setSegSubsDialogOpen}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>Subscriber — {segSubsTarget?.title}</DialogTitle>
              <DialogDescription>Elenco dei subscriber nel segmento.</DialogDescription>
            </DialogHeader>
            {segSubsLoading ? (
              <div className="flex justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin" />
              </div>
            ) : segSubsList.length === 0 ? (
              <p className="text-center text-gray-500 py-8">Nessun subscriber in questo segmento.</p>
            ) : (
              <div className="max-h-80 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Email</TableHead>
                      <TableHead>Nome</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {segSubsList.map((s) => (
                      <TableRow key={s.id ?? s.email}>
                        <TableCell className="font-mono text-sm">{s.email}</TableCell>
                        <TableCell>
                          {s.firstname || s.lastname
                            ? `${s.firstname ?? ""} ${s.lastname ?? ""}`.trim()
                            : "—"
                          }
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setSegSubsDialogOpen(false)}>
                Chiudi
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* --- New field dialog --- */}
        <Dialog open={fieldDialogOpen} onOpenChange={setFieldDialogOpen}>
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle>Nuovo Campo</DialogTitle>
              <DialogDescription>Aggiungi un campo personalizzato ai subscriber.</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateField} className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-1 block">Titolo *</label>
                <Input
                  required
                  value={fieldForm.title}
                  onChange={(e) => setFieldForm((f) => ({ ...f, title: e.target.value }))}
                  placeholder="Nome campo…"
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">Tipo *</label>
                <Select
                  value={fieldForm.type}
                  onValueChange={(v) => setFieldForm((f) => ({ ...f, type: v }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="string">Testo (string)</SelectItem>
                    <SelectItem value="number">Numero (number)</SelectItem>
                    <SelectItem value="date">Data (date)</SelectItem>
                    <SelectItem value="boolean">Booleano (boolean)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setFieldDialogOpen(false)}>
                  Annulla
                </Button>
                <Button type="submit" disabled={fieldSaving || !fieldForm.title.trim()}>
                  {fieldSaving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Crea
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </motion.div>
    </TooltipProvider>
  )
}
