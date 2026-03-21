"use client"

import { useState, useEffect, useCallback } from "react"
import { Plus, Pencil, Trash2, Users, X, Loader2, ArrowLeft } from "lucide-react"
import { motion } from "framer-motion"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { routes } from "@/config/routes"
import {
  listSenderGroups,
  createSenderGroup,
  renameSenderGroup,
  deleteSenderGroup,
  listSenderGroupSubscribers,
} from "@/services/admin/sender"

function TableSkeleton() {
  return Array.from({ length: 4 }).map((_, i) => (
    <TableRow key={i} className="border-neutral-800">
      <TableCell><Skeleton className="h-4 w-36 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-16 bg-zinc-800" /></TableCell>
      <TableCell><Skeleton className="h-4 w-24 bg-zinc-800" /></TableCell>
    </TableRow>
  ))
}

// Drawer showing subscribers for a group
function GroupSubscribersDrawer({ group, onClose }) {
  const [subs, setSubs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    listSenderGroupSubscribers(group.id).then((res) => {
      const data = res?.data ?? res ?? []
      setSubs(Array.isArray(data) ? data : [])
    }).catch(() => setSubs([])).finally(() => setLoading(false))
  }, [group.id])

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onClose])

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-lg bg-zinc-900 border-neutral-800 text-white max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Subscribers — {group.title ?? group.name}</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto mt-2 space-y-1">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
            </div>
          ) : subs.length === 0 ? (
            <p className="text-neutral-500 text-sm text-center py-8">Nessun subscriber in questo gruppo.</p>
          ) : (
            subs.map((s, i) => (
              <div key={s.id ?? i} className="flex items-center justify-between py-1.5 border-b border-neutral-800 last:border-0">
                <span className="text-sm text-white">{s.email}</span>
                <span className="text-xs text-neutral-500">{[s.firstname, s.lastname].filter(Boolean).join(" ")}</span>
              </div>
            ))
          )}
        </div>
        <div className="pt-3">
          <Button variant="ghost" size="sm" onClick={onClose}>Chiudi</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

// Rename modal
function RenameModal({ group, onClose, onRenamed }) {
  const [title, setTitle] = useState(group.title ?? group.name ?? "")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", handler)
    return () => window.removeEventListener("keydown", handler)
  }, [onClose])

  async function handleSubmit(e) {
    e.preventDefault()
    if (!title.trim()) return
    setLoading(true)
    try {
      await renameSenderGroup(group.id, title.trim())
      onRenamed()
      onClose()
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="sm:max-w-sm bg-zinc-900 border-neutral-800 text-white">
        <DialogHeader><DialogTitle>Rinomina gruppo</DialogTitle></DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="space-y-1">
            <Label>Nome</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} required
              className="bg-zinc-800 border-neutral-700 text-white" />
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Salva"}
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={onClose}>Annulla</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default function SenderGroupsPage() {
  const router = useRouter()
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [newTitle, setNewTitle] = useState("")
  const [creating, setCreating] = useState(false)
  const [createLoading, setCreateLoading] = useState(false)
  const [viewGroup, setViewGroup] = useState(null)
  const [renameGroup, setRenameGroup] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await listSenderGroups()
      const data = res?.data ?? res ?? []
      setGroups(Array.isArray(data) ? data : [])
    } catch {
      setError("Impossibile caricare i gruppi.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate(e) {
    e.preventDefault()
    if (!newTitle.trim()) return
    setCreateLoading(true)
    try {
      await createSenderGroup(newTitle.trim())
      setNewTitle("")
      setCreating(false)
      load()
    } finally {
      setCreateLoading(false)
    }
  }

  async function handleDelete(g) {
    if (!confirm(`Eliminare il gruppo "${g.title ?? g.name}"?`)) return
    await deleteSenderGroup(g.id)
    load()
  }

  return (
    <motion.div
      className="space-y-6 pb-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {viewGroup && <GroupSubscribersDrawer group={viewGroup} onClose={() => setViewGroup(null)} />}
      {renameGroup && <RenameModal group={renameGroup} onClose={() => setRenameGroup(null)} onRenamed={load} />}

      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <Button variant="ghost" onClick={() => router.push(routes.admin.sender.campaigns)} className="mb-1 -ml-2">
            <ArrowLeft className="mr-2 h-4 w-4" /> Campagne
          </Button>
          <h1 className="text-3xl md:text-4xl font-bold gradient-text mt-2">Gruppi</h1>
          <p className="text-gray-300">Organizza i subscriber in gruppi.</p>
        </div>
        <Button size="sm" onClick={() => setCreating(true)} className="mt-1 md:mt-10">
          <Plus className="h-4 w-4 mr-1" /> Nuovo gruppo
        </Button>
      </div>

      {/* Stats row */}
      <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
        <Card className="bg-zinc-900 border border-zinc-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-neutral-400">Gruppi</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{groups.length}</div>
          </CardContent>
        </Card>
      </div>

      {creating && (
        <form onSubmit={handleCreate} className="flex gap-2">
          <Input
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Nome gruppo"
            required
            autoFocus
            className="bg-zinc-800 border-neutral-700 text-white"
          />
          <Button type="submit" size="sm" disabled={createLoading}>
            {createLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Crea"}
          </Button>
          <Button type="button" variant="ghost" size="sm" onClick={() => setCreating(false)}>
            <X className="h-4 w-4" />
          </Button>
        </form>
      )}

      {error && <p className="text-red-400 text-sm">{error}</p>}

      <Card className="bg-zinc-900 border border-zinc-700">
        <CardContent className="p-0">
          <div className="rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-neutral-800 hover:bg-transparent">
                  <TableHead className="text-neutral-400">Nome</TableHead>
                  <TableHead className="text-neutral-400">Subscribers</TableHead>
                  <TableHead className="text-neutral-400 text-right">Azioni</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableSkeleton />
                ) : groups.length === 0 ? (
                  <TableRow className="border-neutral-800">
                    <TableCell colSpan={3} className="text-center text-neutral-500 py-12">
                      Nessun gruppo. Creane uno per iniziare.
                    </TableCell>
                  </TableRow>
                ) : (
                  groups.map((g) => (
                    <TableRow key={g.id} className="border-neutral-800 hover:bg-white/5">
                      <TableCell className="text-white font-medium">{g.title ?? g.name}</TableCell>
                      <TableCell>
                        <span className="text-sm text-neutral-400">
                          {g.count != null ? g.count.toLocaleString() : "—"}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-2">
                          <button onClick={() => setViewGroup(g)} title="Vedi subscribers"
                            className="text-blue-400 hover:text-blue-300">
                            <Users className="h-4 w-4" />
                          </button>
                          <button onClick={() => setRenameGroup(g)} title="Rinomina"
                            className="text-neutral-400 hover:text-neutral-200">
                            <Pencil className="h-4 w-4" />
                          </button>
                          <button onClick={() => handleDelete(g)} title="Elimina"
                            className="text-red-400 hover:text-red-300">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
